"""Tests de HU-05: exportación de reservas a CSV."""
import os

# Misma base aislada que test_booking.py (la primera en importarse fija el motor).
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/citafacil_test.db")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

import csv  # noqa: E402
import io  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.export import HEADER  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
ADMIN = {"X-Admin-Token": "test-token"}
URL = "/api/admin/appointments/export"


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Service(name="Corte", duration_min=30, price=8000, active=True))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _cita(dia: str, hora: int, nombre="Camila", status=models.STATUS_CONFIRMED, notas=""):
    inicio = datetime.fromisoformat(f"{dia}T{hora:02d}:00")
    db = SessionLocal()
    db.add(models.Appointment(
        customer_name=nombre, customer_phone="+56942916570", service_id=1,
        start_at=inicio, end_at=inicio + timedelta(minutes=30), status=status, notes=notas,
    ))
    db.commit()
    db.close()


def _rows(r) -> list[dict]:
    text = r.content.decode("utf-8-sig")  # quita el BOM
    return list(csv.DictReader(io.StringIO(text)))


def test_export_requires_admin_token():
    assert client.get(URL).status_code == 422  # falta cabecera
    assert client.get(URL, headers={"X-Admin-Token": "malo"}).status_code == 401


def test_export_is_a_downloadable_csv_with_bom():
    r = client.get(URL, headers=ADMIN)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="reservas_' in r.headers["content-disposition"]
    assert r.content.startswith("﻿".encode("utf-8"))  # Excel reconoce UTF-8


def test_export_without_appointments_has_only_header():
    r = client.get(URL, headers=ADMIN)
    lines = r.content.decode("utf-8-sig").splitlines()
    assert lines == [",".join(HEADER)]


def test_export_row_content():
    _cita("2026-11-02", 11, nombre="José Muñoz", notas="Primera vez")
    rows = _rows(client.get(URL, headers=ADMIN))
    assert len(rows) == 1
    row = rows[0]
    assert row["fecha"] == "2026-11-02"
    assert row["hora_inicio"] == "11:00" and row["hora_fin"] == "11:30"
    assert row["servicio"] == "Corte" and row["precio"] == "8000"
    assert row["cliente"] == "José Muñoz"  # tildes y eñes intactas
    assert row["celular"] == "+56942916570"
    assert row["estado"] == "Confirmada"
    assert row["notas"] == "Primera vez"
    assert row["recordatorio_enviado"] == "no"


def test_export_is_sorted_by_date():
    _cita("2026-11-03", 10, nombre="Segunda")
    _cita("2026-11-02", 15, nombre="Primera")
    rows = _rows(client.get(URL, headers=ADMIN))
    assert [r["cliente"] for r in rows] == ["Primera", "Segunda"]


def test_export_filter_by_status():
    _cita("2026-11-02", 10, nombre="Ana", status=models.STATUS_PENDING)
    _cita("2026-11-02", 11, nombre="Beto", status=models.STATUS_CANCELLED)
    rows = _rows(client.get(URL, params={"status": "cancelled"}, headers=ADMIN))
    assert [r["cliente"] for r in rows] == ["Beto"]
    assert rows[0]["estado"] == "Cancelada"


def test_export_filter_by_date_range_is_inclusive():
    _cita("2026-11-01", 19, nombre="Antes")
    _cita("2026-11-02", 10, nombre="Desde")
    _cita("2026-11-04", 19, nombre="Hasta")  # último día del rango, tarde
    _cita("2026-11-05", 10, nombre="Despues")
    rows = _rows(client.get(URL, params={"date_from": "2026-11-02", "date_to": "2026-11-04"}, headers=ADMIN))
    assert [r["cliente"] for r in rows] == ["Desde", "Hasta"]


def test_export_neutralizes_formulas():
    """Un nombre o nota que empiece con = + - @ no debe ejecutarse como fórmula en Excel."""
    _cita("2026-11-02", 10, nombre="=HYPERLINK(\"http://x\",\"clic\")", notas="@SUM(A1)")
    row = _rows(client.get(URL, headers=ADMIN))[0]
    assert row["cliente"].startswith("'=")
    assert row["notas"] == "'@SUM(A1)"
    assert row["celular"] == "+56942916570"  # el celular normalizado no se toca


def test_export_rejects_invalid_filters():
    assert client.get(URL, params={"status": "borrado"}, headers=ADMIN).status_code == 422
    assert client.get(URL, params={"date_from": "2026-11-05", "date_to": "2026-11-01"},
                      headers=ADMIN).status_code == 422
    assert client.get(URL, params={"date_from": "no-es-fecha"}, headers=ADMIN).status_code == 422


def test_admin_list_still_filters_by_single_day():
    """El listado del panel sigue funcionando igual tras ampliar list_appointments."""
    _cita("2026-11-02", 10, nombre="Ana")
    _cita("2026-11-03", 10, nombre="Beto")
    r = client.get("/api/admin/appointments", params={"date": "2026-11-03"}, headers=ADMIN)
    assert [a["customer_name"] for a in r.json()] == ["Beto"]
