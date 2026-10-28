"""Siembra datos de ejemplo (una barbería) para la demo.

Uso:
    python seed.py                         # servicios + 2 citas de ejemplo (futuras)
    python seed.py --historico             # además, ~8 semanas de citas pasadas
    python seed.py --historico --dias 90   # ventana de histórico distinta

El histórico existe para poder ver los gráficos de previsión de la demanda: la app no deja
reservar en el pasado, así que sin esto el histórico siempre estaría vacío. Es determinista
(misma semilla = mismos datos) y no se vuelve a crear si ya hay citas pasadas.
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.utils import local_now, normalize_cl_phone

SERVICES = [
    {"name": "Corte de pelo", "duration_min": 30, "price": 8000},
    {"name": "Corte + Barba", "duration_min": 45, "price": 12000},
    {"name": "Perfilado de barba", "duration_min": 20, "price": 6000},
    {"name": "Corte niño", "duration_min": 25, "price": 6500},
    {"name": "Tinte / Color", "duration_min": 60, "price": 18000},
]

# --- Parámetros del histórico de ejemplo ---
# Reservas típicas por día de la semana (0 = lunes ... 6 = domingo): el fin de semana rinde más.
DEMAND_BY_WEEKDAY = {0: 5, 1: 5, 2: 6, 3: 7, 4: 10, 5: 12, 6: 0}
# Qué tan seguido se pide cada servicio (los más baratos y rápidos se piden más).
SERVICE_WEIGHT = {
    "Corte de pelo": 5, "Corte + Barba": 4, "Perfilado de barba": 3, "Corte niño": 2, "Tinte / Color": 1,
}
CANCEL_RATE = 0.08          # fracción de citas pasadas que quedaron canceladas
DEFAULT_HISTORY_DAYS = 56   # 8 semanas
DEFAULT_RNG_SEED = 42

_NOMBRES = ["Camila", "Diego", "Valentina", "Matías", "Francisca", "Joaquín", "Javiera", "Sebastián",
            "Antonia", "Benjamín", "Constanza", "Nicolás", "Fernanda", "Tomás", "Catalina", "Felipe"]
_APELLIDOS = ["Rojas", "Soto", "Muñoz", "Pérez", "González", "Silva", "Contreras", "Díaz",
              "Morales", "Vega", "Fuentes", "Castro"]


def _next_open_day(hour: int):
    d = (local_now() + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
    while d.weekday() in settings.closed_weekdays_set:
        d += timedelta(days=1)
    return d


def seed_services(db: Session) -> bool:
    """Crea los servicios de ejemplo si no existe ninguno. Devuelve True si los creó."""
    if db.query(models.Service).count() != 0:
        return False
    for s in SERVICES:
        db.add(models.Service(**s))
    db.commit()
    return True


def seed_examples(db: Session) -> bool:
    """Crea 2 citas futuras de ejemplo si la tabla de citas está vacía."""
    if db.query(models.Appointment).count() != 0:
        return False
    corte = db.query(models.Service).filter_by(name="Corte de pelo").first()
    barba = db.query(models.Service).filter_by(name="Corte + Barba").first()
    base = _next_open_day(11)
    ejemplos = [
        ("Camila Rojas", "+56 9 8765 4321", corte, base),
        ("Diego Soto", "+56 9 1234 5678", barba, base.replace(hour=12)),
    ]
    for name, phone, svc, start in ejemplos:
        db.add(
            models.Appointment(
                customer_name=name,
                customer_phone=normalize_cl_phone(phone),
                service_id=svc.id,
                start_at=start,
                end_at=start + timedelta(minutes=svc.duration_min),
                status=models.STATUS_CONFIRMED,
            )
        )
    db.commit()
    return True


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def seed_history(
    db: Session, days: int = DEFAULT_HISTORY_DAYS, rng_seed: int = DEFAULT_RNG_SEED
) -> int:
    """Crea citas pasadas (desde hace `days` días hasta ayer) con un patrón de demanda realista.

    - Respeta el horario del negocio, los días cerrados y que no haya citas solapadas.
    - La demanda depende del día de la semana y crece suavemente hacia el presente.
    - Casi todas quedan como 'done'; una fracción (CANCEL_RATE) como 'cancelled'.
    Devuelve cuántas creó; 0 si ya existía histórico o no hay servicios.
    """
    today = local_now().date()
    if db.query(models.Appointment).filter(
        models.Appointment.start_at < datetime.combine(today, time.min)
    ).count():
        return 0
    services = db.query(models.Service).filter_by(active=True).order_by(models.Service.id).all()
    if not services:
        return 0

    rng = random.Random(rng_seed)
    weights = [SERVICE_WEIGHT.get(s.name, 1) for s in services]
    clientes = [
        (f"{n} {a}", normalize_cl_phone(f"9 {rng.randint(5000, 9999)} {rng.randint(1000, 9999)}"))
        for n in _NOMBRES for a in rng.sample(_APELLIDOS, 2)
    ]
    step = timedelta(minutes=settings.slot_interval_minutes)

    created = 0
    for offset in range(days, 0, -1):
        day = today - timedelta(days=offset)
        if day.weekday() in settings.closed_weekdays_set:
            continue
        trend = 0.85 + 0.30 * (days - offset) / max(days - 1, 1)  # de 0.85x a 1.15x
        n = max(0, round(rng.gauss(DEMAND_BY_WEEKDAY[day.weekday()] * trend, 1.2)))
        open_dt = datetime.combine(day, time(hour=settings.open_hour))
        close_dt = datetime.combine(day, time(hour=settings.close_hour))
        taken: list[tuple[datetime, datetime]] = []
        for _ in range(n):
            svc = rng.choices(services, weights=weights)[0]
            dur = timedelta(minutes=svc.duration_min)
            candidatos = []
            cursor = open_dt
            while cursor + dur <= close_dt:
                if not any(_overlaps(cursor, cursor + dur, a, b) for a, b in taken):
                    candidatos.append(cursor)
                cursor += step
            if not candidatos:
                break  # el día está lleno
            start = rng.choice(candidatos)
            taken.append((start, start + dur))
            nombre, telefono = rng.choice(clientes)
            cancelled = rng.random() < CANCEL_RATE
            db.add(
                models.Appointment(
                    customer_name=nombre,
                    customer_phone=telefono,
                    service_id=svc.id,
                    start_at=start,
                    end_at=start + dur,
                    status=models.STATUS_CANCELLED if cancelled else models.STATUS_DONE,
                    reminder_sent=not cancelled,
                    created_at=start - timedelta(days=rng.randint(1, 5)),
                )
            )
            created += 1
    db.commit()
    return created


def run(historico: bool = False, dias: int = DEFAULT_HISTORY_DAYS) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if seed_services(db):
            print(f"✔ Sembrados {len(SERVICES)} servicios.")
        else:
            print("• Ya existen servicios; no se vuelve a sembrar.")

        if seed_examples(db):
            print("✔ Citas de ejemplo creadas.")
        else:
            print("• Ya existen citas; no se crean ejemplos.")

        if historico:
            n = seed_history(db, days=dias)
            if n:
                print(f"✔ Histórico creado: {n} citas pasadas en los últimos {dias} días.")
            else:
                print("• Ya existe histórico (o no hay servicios); no se vuelve a crear.")
    finally:
        db.close()


def main() -> None:
    # En consolas de Windows (cp1252) imprimir ✔ lanza UnicodeEncodeError y corta el script.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Siembra datos de ejemplo para CitaFácil.")
    parser.add_argument("--historico", action="store_true",
                        help="crea además citas pasadas (para ver los gráficos de previsión)")
    parser.add_argument("--dias", type=int, default=DEFAULT_HISTORY_DAYS,
                        help=f"días de histórico a crear (por defecto {DEFAULT_HISTORY_DAYS})")
    args = parser.parse_args()
    run(historico=args.historico, dias=max(7, args.dias))


if __name__ == "__main__":
    main()
