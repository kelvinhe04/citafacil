"""Exportación de reservas a CSV para abrirlas en una hoja de cálculo (HU-05)."""
from __future__ import annotations

import csv
import io

from . import models
from .utils import local_now

STATUS_LABELS = {
    models.STATUS_PENDING: "Pendiente",
    models.STATUS_CONFIRMED: "Confirmada",
    models.STATUS_CANCELLED: "Cancelada",
    models.STATUS_DONE: "Realizada",
}

HEADER = [
    "id", "fecha", "hora_inicio", "hora_fin", "servicio", "precio", "cliente",
    "celular", "estado", "notas", "recordatorio_enviado", "creada_utc",
]

# Si una celda empieza con estos caracteres, Excel/Sheets la interpretan como fórmula.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_text(value: str) -> str:
    """Evita la inyección de fórmulas en el texto libre que escribe el cliente."""
    value = value or ""
    return "'" + value if value.startswith(_FORMULA_PREFIXES) else value


def appointments_to_csv(appointments: list[models.Appointment]) -> str:
    """CSV con una fila por cita. Incluye BOM para que Excel muestre bien tildes y eñes."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(HEADER)
    for a in appointments:
        writer.writerow([
            a.id,
            a.start_at.strftime("%Y-%m-%d"),
            a.start_at.strftime("%H:%M"),
            a.end_at.strftime("%H:%M"),
            _safe_text(a.service.name if a.service else ""),
            a.service.price if a.service else "",
            _safe_text(a.customer_name),
            a.customer_phone,  # ya normalizado a +569XXXXXXXX por el backend
            STATUS_LABELS.get(a.status, a.status),
            _safe_text(a.notes),
            "sí" if a.reminder_sent else "no",
            a.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    return "\ufeff" + buf.getvalue()


def csv_filename() -> str:
    return f"reservas_{local_now():%Y-%m-%d}.csv"
