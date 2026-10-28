"""Tests de HU-04: cancelar o reprogramar una cita desde un enlace (autogestión)."""
import os

# Misma base de datos de prueba aislada que test_booking.py (antes de importar la app).
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/citafacil_test.db")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

from datetime import timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.manage import make_token  # noqa: E402
from app.utils import local_now  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Service(name="Corte", duration_min=30, price=8000, active=True))
    db.add(models.Service(name="Tratamiento largo", duration_min=60, price=20000, active=True))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _next_open_day_at(hour: int):
    d = (local_now() + timedelta(days=2)).replace(hour=hour, minute=0, second=0, microsecond=0)
    while d.weekday() == 6:  # saltar domingo
        d += timedelta(days=1)
    return d


def _services():
    s = client.get("/api/services").json()
    return {x["name"]: x["id"] for x in s}


def _book(start, service="Corte", name="Camila", phone="+56 9 4291 6570"):
    r = client.post(
        "/api/appointments",
        json={"customer_name": name, "customer_phone": phone,
              "service_id": _services()[service], "start_at": start.isoformat()},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _slots(service, day):
    return client.get(f"/api/availability?service_id={_services()[service]}&date={day.date().isoformat()}").json()


# ---------- Token ----------
def test_booking_returns_manage_token_and_link_works():
    appt = _book(_next_open_day_at(11))
    token = appt["manage_token"]
    assert token and token.startswith(f"{appt['id']}-")

    r = client.get(f"/api/manage/{token}")
    assert r.status_code == 200
    assert r.json()["id"] == appt["id"]
    assert r.json()["can_change"] is True


@pytest.mark.parametrize("bad", ["abc", "1-", "-abc", "999-deadbeef", "x-y"])
def test_malformed_or_unknown_token_is_404(bad):
    _book(_next_open_day_at(11))
    assert client.get(f"/api/manage/{bad}").status_code == 404


def test_tampered_signature_is_rejected():
    appt = _book(_next_open_day_at(11))
    forged = f"{appt['id']}-{'0' * 24}"
    assert client.get(f"/api/manage/{forged}").status_code == 404
    assert client.post(f"/api/manage/{forged}/cancel").status_code == 404


def test_token_of_one_appointment_does_not_open_another():
    a = _book(_next_open_day_at(11), name="Ana", phone="942916570")
    b = _book(_next_open_day_at(13), name="Beto", phone="987654321")
    sig_a = a["manage_token"].split("-", 1)[1]
    assert client.get(f"/api/manage/{b['id']}-{sig_a}").status_code == 404


def test_admin_listing_does_not_expose_manage_token():
    _book(_next_open_day_at(11))
    rows = client.get("/api/admin/appointments", headers={"X-Admin-Token": "test-token"}).json()
    assert rows and all("manage_token" not in row for row in rows)


# ---------- Cancelar ----------
def test_cancel_frees_the_slot_and_cannot_be_repeated():
    start = _next_open_day_at(11)
    appt = _book(start)
    assert "11:00" not in _slots("Corte", start)

    r = client.post(f"/api/manage/{appt['manage_token']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    assert r.json()["can_change"] is False
    assert "11:00" in _slots("Corte", start)  # el horario vuelve a quedar disponible

    # ya cancelada: no se puede cancelar ni reprogramar de nuevo
    assert client.post(f"/api/manage/{appt['manage_token']}/cancel").status_code == 403
    r2 = client.post(f"/api/manage/{appt['manage_token']}/reschedule",
                     json={"start_at": _next_open_day_at(15).isoformat()})
    assert r2.status_code == 403


# ---------- Reprogramar ----------
def test_reschedule_moves_the_appointment_and_resets_reminder():
    start = _next_open_day_at(11)
    new_start = _next_open_day_at(15)
    appt = _book(start)

    db = SessionLocal()  # simula que el recordatorio ya se había enviado
    db.query(models.Appointment).filter_by(id=appt["id"]).update({"reminder_sent": True})
    db.commit()
    db.close()

    r = client.post(f"/api/manage/{appt['manage_token']}/reschedule", json={"start_at": new_start.isoformat()})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["start_at"].startswith(new_start.strftime("%Y-%m-%dT%H:%M"))
    assert body["end_at"].startswith((new_start + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M"))
    assert body["reminder_sent"] is False
    assert body["status"] in ("pending", "confirmed")

    assert "11:00" in _slots("Corte", start)      # el horario viejo se liberó
    assert "15:00" not in _slots("Corte", start)  # el nuevo quedó ocupado


def test_reschedule_to_a_taken_slot_returns_409():
    a = _book(_next_open_day_at(11), name="Ana", phone="942916570")
    _book(_next_open_day_at(13), name="Beto", phone="987654321")
    r = client.post(f"/api/manage/{a['manage_token']}/reschedule",
                    json={"start_at": _next_open_day_at(13).isoformat()})
    assert r.status_code == 409


def test_reschedule_may_overlap_its_own_old_slot():
    """Un tratamiento de 60 min a las 11:00 puede moverse a las 11:30 aunque se solapen:
    la cita propia no debe bloquearse a sí misma."""
    start = _next_open_day_at(11)
    appt = _book(start, service="Tratamiento largo")
    assert "11:30" not in _slots("Tratamiento largo", start)  # público: lo ve ocupado

    mine = client.get(f"/api/manage/{appt['manage_token']}/availability?date={start.date().isoformat()}").json()
    assert "11:30" in mine  # para su dueño, sí está libre

    r = client.post(f"/api/manage/{appt['manage_token']}/reschedule",
                    json={"start_at": (start + timedelta(minutes=30)).isoformat()})
    assert r.status_code == 200, r.text


def test_reschedule_outside_business_hours_is_rejected():
    appt = _book(_next_open_day_at(11))
    r = client.post(f"/api/manage/{appt['manage_token']}/reschedule",
                    json={"start_at": _next_open_day_at(22).isoformat()})
    assert r.status_code == 409


# ---------- Regla de anticipación ----------
def test_cannot_change_inside_the_minimum_notice_window():
    db = SessionLocal()
    soon = local_now() + timedelta(hours=1)  # menos de MANAGE_MIN_HOURS_BEFORE (2 h)
    appt = models.Appointment(
        customer_name="Urgente", customer_phone="+56942916570", service_id=1,
        start_at=soon, end_at=soon + timedelta(minutes=30), status=models.STATUS_PENDING,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    token = make_token(appt)
    db.close()

    view = client.get(f"/api/manage/{token}").json()
    assert view["can_change"] is False
    assert "horas antes" in view["change_blocked_reason"]
    assert client.post(f"/api/manage/{token}/cancel").status_code == 403
    assert client.post(f"/api/manage/{token}/reschedule",
                       json={"start_at": _next_open_day_at(15).isoformat()}).status_code == 403
