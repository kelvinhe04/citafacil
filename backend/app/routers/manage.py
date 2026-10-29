"""Endpoints de autogestión: el cliente cancela o reprograma su cita con el enlace firmado."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..availability import generate_slots, is_slot_free
from ..config import settings
from ..database import get_db
from ..manage import appointment_from_token, change_block_reason
from ..notifications import cancellation_message, reschedule_message, send_whatsapp

router = APIRouter(prefix="/api/manage", tags=["Autogestión de citas"])


def _get_or_404(db: Session, token: str) -> models.Appointment:
    appt = appointment_from_token(db, token)
    if appt is None:
        # Mismo mensaje para "no existe" y "firma inválida": no revela si la cita existe.
        raise HTTPException(status_code=404, detail="Enlace inválido o cita no encontrada.")
    return appt


def _require_changeable(appt: models.Appointment) -> None:
    reason = change_block_reason(appt)
    if reason:
        raise HTTPException(status_code=403, detail=reason)


def _view(appt: models.Appointment) -> schemas.ManageOut:
    reason = change_block_reason(appt)
    out = schemas.ManageOut.model_validate(appt)
    out.can_change = not reason
    out.change_blocked_reason = reason
    return out


@router.get("/{token}", response_model=schemas.ManageOut, summary="Ver mi cita")
def get_my_appointment(token: str, db: Session = Depends(get_db)):
    return _view(_get_or_404(db, token))


@router.get("/{token}/availability", response_model=list[str], summary="Horarios libres para reprogramar")
def my_availability(
    token: str,
    day: date = Query(..., alias="date", description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    appt = _get_or_404(db, token)
    _require_changeable(appt)
    # exclude_id: la propia cita no debe bloquear sus horarios vecinos.
    return generate_slots(db, appt.service, day, exclude_id=appt.id)


@router.post("/{token}/cancel", response_model=schemas.ManageOut, summary="Cancelar mi cita")
def cancel_my_appointment(token: str, db: Session = Depends(get_db)):
    appt = _get_or_404(db, token)
    _require_changeable(appt)
    appt = crud.set_status(db, appt, models.STATUS_CANCELLED)
    send_whatsapp(
        appt.customer_phone,
        cancellation_message(settings.business_name, appt.customer_name, appt.service.name, appt.start_at),
    )
    return _view(appt)


@router.post("/{token}/reschedule", response_model=schemas.ManageOut, summary="Reprogramar mi cita")
def reschedule_my_appointment(token: str, payload: schemas.RescheduleIn, db: Session = Depends(get_db)):
    appt = _get_or_404(db, token)
    _require_changeable(appt)
    service = appt.service
    if not is_slot_free(db, service, payload.start_at, exclude_id=appt.id):
        raise HTTPException(
            status_code=409,
            detail="Ese horario ya no está disponible. Por favor elige otro.",
        )
    end_at = payload.start_at + timedelta(minutes=service.duration_min)
    appt = crud.reschedule_appointment(db, appt, payload.start_at, end_at)
    send_whatsapp(
        appt.customer_phone,
        reschedule_message(settings.business_name, appt.customer_name, service.name, appt.start_at),
    )
    return _view(appt)
