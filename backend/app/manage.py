"""Autogestión de citas: enlace firmado para cancelar o reprogramar sin llamar al negocio.

El token es "<id>-<firma>", donde la firma es un HMAC-SHA256 de la cita. No se guarda
en la base de datos (no requiere cambios de esquema) y no se puede adivinar sin la clave.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from . import crud, models
from .config import settings
from .utils import local_now


def _sign(appt_id: int, phone: str) -> str:
    msg = f"{appt_id}:{phone}".encode()
    return hmac.new(settings.manage_key.encode(), msg, hashlib.sha256).hexdigest()[:24]


def make_token(appt: models.Appointment) -> str:
    return f"{appt.id}-{_sign(appt.id, appt.customer_phone)}"


def manage_url(appt: models.Appointment) -> str:
    """Enlace público para gestionar la cita ('' si no hay FRONTEND_URL configurada)."""
    if not settings.frontend_url:
        return ""
    return f"{settings.frontend_url.rstrip('/')}/manage.html?t={make_token(appt)}"


def appointment_from_token(db: Session, token: str) -> Optional[models.Appointment]:
    """Devuelve la cita si el token es válido; None si está mal formado o la firma no coincide."""
    id_part, sep, sig = (token or "").partition("-")
    if not sep or not id_part.isdigit():
        return None
    appt = crud.get_appointment(db, int(id_part))
    if appt is None:
        return None
    if not hmac.compare_digest(sig, _sign(appt.id, appt.customer_phone)):
        return None
    return appt


def change_block_reason(appt: models.Appointment) -> str:
    """'' si la cita se puede cancelar/reprogramar; si no, el motivo para mostrar al cliente."""
    if appt.status not in (models.STATUS_PENDING, models.STATUS_CONFIRMED):
        return "Esta cita ya no se puede modificar."
    limit = local_now() + timedelta(hours=settings.manage_min_hours_before)
    if appt.start_at < limit:
        return (
            f"Solo puedes cambiar tu cita hasta {settings.manage_min_hours_before} horas antes. "
            "Contacta al negocio."
        )
    return ""
