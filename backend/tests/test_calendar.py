"""Tests de HU-02: calendario dinámico con la disponibilidad del mes."""
import os

# Misma base aislada que test_booking.py (la primera en importarse fija el motor).
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/citafacil_test.db")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

import calendar  # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.availability import month_availability  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.utils import local_now  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Service(name="Corte", duration_min=30, price=8000, active=True))
    db.add(models.Service(name="Inactivo", duration_min=30, price=1000, active=False))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _next_month() -> tuple[int, int]:
    """Mes siguiente al actual: todos sus días son futuros."""
    first = local_now().date().replace(day=1)
    nxt = first + timedelta(days=32)
    return nxt.year, nxt.month


def _month_param(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _first_open_day(year: int, month: int) -> date:
    d = date(year, month, 1)
    while d.weekday() == 6:  # domingo cerrado por defecto
        d += timedelta(days=1)
    return d


def _book(day: date, start_hour: int, end_hour: int, status=models.STATUS_CONFIRMED):
    db = SessionLocal()
    db.add(models.Appointment(
        customer_name="Cliente", customer_phone="+56912345678", service_id=1,
        start_at=datetime(day.year, day.month, day.day, start_hour),
        end_at=datetime(day.year, day.month, day.day, end_hour),
        status=status,
    ))
    db.commit()
    db.close()


def _get_month(year: int, month: int, service_id: int = 1):
    return client.get(
        f"/api/availability/month?service_id={service_id}&month={_month_param(year, month)}"
    )


# ---------- Endpoint ----------
def test_month_returns_every_day_of_the_month():
    year, month = _next_month()
    r = _get_month(year, month)
    assert r.status_code == 200, r.text
    days = r.json()
    assert len(days) == calendar.monthrange(year, month)[1]
    assert days[0]["date"] == date(year, month, 1).isoformat()
    assert {d["status"] for d in days} <= {"past", "closed", "full", "available"}


def test_sundays_are_closed_and_weekdays_available():
    year, month = _next_month()
    for d in _get_month(year, month).json():
        weekday = date.fromisoformat(d["date"]).weekday()
        if weekday == 6:
            assert d["status"] == "closed" and d["free_slots"] == 0
        else:
            assert d["status"] == "available" and d["free_slots"] > 0


def test_free_slots_match_daily_availability():
    """El calendario reutiliza generate_slots: el conteo coincide con /api/availability."""
    year, month = _next_month()
    day = _first_open_day(year, month)
    _book(day, 11, 12)  # ocupa 11:00 y 11:30

    cal = {d["date"]: d for d in _get_month(year, month).json()}
    slots = client.get(f"/api/availability?service_id=1&date={day.isoformat()}").json()
    assert cal[day.isoformat()]["free_slots"] == len(slots)
    assert "11:00" not in slots


def test_fully_booked_day_is_full():
    year, month = _next_month()
    day = _first_open_day(year, month)
    _book(day, 10, 20)  # todo el horario de atención (10:00-20:00)

    cal = {d["date"]: d for d in _get_month(year, month).json()}
    assert cal[day.isoformat()] == {"date": day.isoformat(), "status": "full", "free_slots": 0}


def test_cancelled_appointment_does_not_block_day():
    year, month = _next_month()
    day = _first_open_day(year, month)
    _book(day, 10, 20, status=models.STATUS_CANCELLED)

    cal = {d["date"]: d for d in _get_month(year, month).json()}
    assert cal[day.isoformat()]["status"] == "available"


def test_past_days_are_marked_past():
    year, month = _next_month()
    db = SessionLocal()
    service = db.get(models.Service, 1)
    # "Hoy" simulado a mitad del mes: los días anteriores salen como pasados.
    days = month_availability(db, service, year, month, today=date(year, month, 15))
    db.close()
    assert all(d["status"] == "past" and d["free_slots"] == 0 for d in days[:14])
    assert all(d["status"] != "past" for d in days[14:])


def test_february_leap_year_has_29_days():
    db = SessionLocal()
    service = db.get(models.Service, 1)
    days = month_availability(db, service, 2028, 2, today=date(2028, 1, 1))
    db.close()
    assert len(days) == 29


# ---------- Validación ----------
@pytest.mark.parametrize("bad", ["2026-13", "2026-1", "26-01", "0000-05", "2026/05", "abc"])
def test_invalid_month_format_is_rejected(bad):
    r = client.get(f"/api/availability/month?service_id=1&month={bad}")
    assert r.status_code == 422


def test_unknown_or_inactive_service_returns_404():
    year, month = _next_month()
    assert _get_month(year, month, service_id=999).status_code == 404
    assert _get_month(year, month, service_id=2).status_code == 404  # servicio inactivo
