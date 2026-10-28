"""Tests de HU-03: histórico y previsión de la demanda."""
import os

# Misma base aislada que test_booking.py (la primera en importarse fija el motor).
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/citafacil_test.db")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

from datetime import date, datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.forecast import build_forecast  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
HOY = date(2026, 10, 28)  # miércoles


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    session.add(models.Service(name="Corte", duration_min=30, price=8000, active=True))
    session.add(models.Service(name="Barba", duration_min=30, price=5000, active=True))
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _cita(db, dia: date, service_id=1, status=models.STATUS_CONFIRMED, hora=11):
    inicio = datetime(dia.year, dia.month, dia.day, hora)
    db.add(models.Appointment(
        customer_name="Cliente", customer_phone="+56912345678", service_id=service_id,
        start_at=inicio, end_at=inicio + timedelta(minutes=30), status=status,
    ))
    db.commit()


def test_sin_datos_devuelve_ceros(db):
    f = build_forecast(db, history_days=14, horizon_days=7, today=HOY)
    assert f["total_history"] == 0
    assert len(f["daily"]) == 14
    assert len(f["forecast"]) == 7
    assert all(x["expected"] == 0 for x in f["forecast"])
    assert f["by_service"] == []


def test_canceladas_no_cuentan(db):
    _cita(db, HOY - timedelta(days=1))
    _cita(db, HOY - timedelta(days=1), status=models.STATUS_CANCELLED)
    f = build_forecast(db, history_days=14, horizon_days=7, today=HOY)
    assert f["total_history"] == 1


def test_citas_fuera_de_ventana_se_ignoran(db):
    _cita(db, HOY - timedelta(days=30))
    _cita(db, HOY + timedelta(days=1))  # futuro: no es histórico
    f = build_forecast(db, history_days=14, horizon_days=7, today=HOY)
    assert f["total_history"] == 0


def test_promedio_por_dia_de_la_semana(db):
    # 14 días de histórico = 2 apariciones de cada día. Dos lunes con 2 y 0 citas.
    lunes = HOY - timedelta(days=HOY.weekday())  # lunes de esta semana
    _cita(db, lunes)
    _cita(db, lunes, hora=12)
    f = build_forecast(db, history_days=14, horizon_days=14, today=HOY)
    assert f["by_weekday"][0]["average"] == 1.0  # 2 citas / 2 lunes
    lunes_futuros = [x for x in f["forecast"] if date.fromisoformat(x["date"]).weekday() == 0]
    assert lunes_futuros and all(x["expected"] == 1.0 for x in lunes_futuros)
    assert f["by_weekday"][1]["average"] == 0.0


def test_agrupa_por_servicio_y_semana(db):
    d = HOY - timedelta(days=2)
    _cita(db, d, service_id=1)
    _cita(db, d, service_id=1, hora=12)
    _cita(db, d, service_id=2, hora=13)
    f = build_forecast(db, history_days=14, horizon_days=7, today=HOY)
    corte, barba = f["by_service"]
    assert (corte["name"], corte["count"], corte["revenue"]) == ("Corte", 2, 16000)
    assert (barba["name"], barba["count"], barba["revenue"]) == ("Barba", 1, 5000)
    assert sum(w["count"] for w in f["weekly"]) == 3


def test_endpoint_requiere_token():
    assert client.get("/api/admin/forecast").status_code == 422  # falta cabecera
    assert client.get(
        "/api/admin/forecast", headers={"X-Admin-Token": "malo"}
    ).status_code == 401


def test_endpoint_valida_parametros_y_responde(db):
    h = {"X-Admin-Token": "test-token"}
    r = client.get("/api/admin/forecast", headers=h)
    assert r.status_code == 200
    assert len(r.json()["forecast"]) == 14
    assert client.get("/api/admin/forecast?horizon_days=0", headers=h).status_code == 422
    assert client.get("/api/admin/forecast?history_days=1000", headers=h).status_code == 422
