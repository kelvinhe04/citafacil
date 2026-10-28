"""Tests del histórico de ejemplo de seed.py (para ver los gráficos de previsión)."""
import os

# Misma base de datos de prueba aislada que los demás tests (antes de importar la app).
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/citafacil_test.db")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

from collections import Counter  # noqa: E402
from datetime import datetime, time, timedelta  # noqa: E402

import pytest  # noqa: E402

import seed  # noqa: E402
from app import models  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.utils import local_now  # noqa: E402

DAYS = 56


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    seed.seed_services(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _all(db):
    return db.query(models.Appointment).order_by(models.Appointment.start_at).all()


def _today_start():
    return datetime.combine(local_now().date(), time.min)


def test_history_only_creates_past_appointments_within_the_window(db):
    n = seed.seed_history(db, days=DAYS)
    rows = _all(db)
    assert n == len(rows) and n > 150  # ~8 semanas de una barbería: cientos de citas
    assert all(a.start_at < _today_start() for a in rows)                          # nada de hoy ni futuro
    assert all(a.start_at >= _today_start() - timedelta(days=DAYS) for a in rows)  # dentro de la ventana


def test_history_respects_business_hours_closed_days_and_never_overlaps(db):
    seed.seed_history(db, days=DAYS)
    by_day = {}
    for a in _all(db):
        assert a.start_at.weekday() not in settings.closed_weekdays_set
        assert a.start_at.hour >= settings.open_hour
        assert a.end_at.hour < settings.close_hour or (a.end_at.hour == settings.close_hour and a.end_at.minute == 0)
        by_day.setdefault(a.start_at.date(), []).append(a)
    for appts in by_day.values():
        appts.sort(key=lambda a: a.start_at)
        for prev, nxt in zip(appts, appts[1:]):
            assert prev.end_at <= nxt.start_at  # sin dobles reservas


def test_history_has_a_realistic_mix_of_statuses_services_and_weekdays(db):
    seed.seed_history(db, days=DAYS)
    rows = _all(db)
    statuses = Counter(a.status for a in rows)
    assert set(statuses) <= {models.STATUS_DONE, models.STATUS_CANCELLED}
    assert 0 < statuses[models.STATUS_CANCELLED] < 0.2 * len(rows)       # algunas canceladas, pocas
    assert len({a.service_id for a in rows}) >= 4                        # varios servicios
    per_wd = Counter(a.start_at.weekday() for a in rows)
    assert per_wd[4] + per_wd[5] > per_wd[0] + per_wd[1]                 # viernes y sábado rinden más
    assert per_wd[6] == 0                                                # domingo cerrado


def test_history_is_deterministic(db):
    seed.seed_history(db, days=DAYS, rng_seed=7)
    first = [(a.start_at, a.service_id, a.status, a.customer_phone) for a in _all(db)]

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed.seed_services(db)
    seed.seed_history(db, days=DAYS, rng_seed=7)
    second = [(a.start_at, a.service_id, a.status, a.customer_phone) for a in _all(db)]
    assert first == second


def test_history_is_idempotent(db):
    seed.seed_history(db, days=DAYS)
    before = db.query(models.Appointment).count()
    assert seed.seed_history(db, days=DAYS) == 0
    assert db.query(models.Appointment).count() == before


def test_history_keeps_the_future_example_appointments(db):
    assert seed.seed_examples(db) is True
    seed.seed_history(db, days=DAYS)
    futuras = [a for a in _all(db) if a.start_at >= _today_start()]
    assert len(futuras) == 2 and all(a.status == models.STATUS_CONFIRMED for a in futuras)


def test_history_without_services_creates_nothing():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        assert seed.seed_history(session, days=DAYS) == 0
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
