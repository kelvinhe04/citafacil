"""Histórico y previsión de la demanda (HU-03).

La previsión es un promedio simple por día de la semana: para cada día futuro se
promedia la cantidad de reservas de ese mismo día de la semana en el histórico.
Las citas canceladas no cuentan como demanda.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from . import models
from .utils import local_now

WEEKDAY_NAMES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def build_forecast(
    db: Session, history_days: int = 56, horizon_days: int = 14, today: date | None = None
) -> dict:
    today = today or local_now().date()
    start = today - timedelta(days=history_days - 1)

    rows = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.start_at >= datetime.combine(start, time.min),
            models.Appointment.start_at <= datetime.combine(today, time.max),
            models.Appointment.status != models.STATUS_CANCELLED,
        )
        .all()
    )

    per_day: Counter = Counter()
    per_week: Counter = Counter()
    per_service: dict[int, dict] = defaultdict(lambda: {"name": "", "count": 0, "revenue": 0})
    for a in rows:
        d = a.start_at.date()
        per_day[d] += 1
        per_week[_monday(d)] += 1
        svc = per_service[a.service_id]
        svc["name"] = a.service.name if a.service else f"#{a.service_id}"
        svc["count"] += 1
        svc["revenue"] += a.service.price if a.service else 0

    daily = [
        {"date": (start + timedelta(days=i)).isoformat(), "count": per_day[start + timedelta(days=i)]}
        for i in range(history_days)
    ]

    weeks = []
    w = _monday(start)
    while w <= today:
        weeks.append({"week_start": w.isoformat(), "count": per_week[w]})
        w += timedelta(days=7)

    # Promedio por día de la semana sobre todos los días del histórico (incluye ceros).
    totals = [0] * 7
    occurrences = [0] * 7
    for i in range(history_days):
        d = start + timedelta(days=i)
        totals[d.weekday()] += per_day[d]
        occurrences[d.weekday()] += 1
    avg = [round(totals[i] / occurrences[i], 2) if occurrences[i] else 0.0 for i in range(7)]

    forecast = []
    for i in range(1, horizon_days + 1):
        d = today + timedelta(days=i)
        forecast.append({"date": d.isoformat(), "expected": avg[d.weekday()]})

    return {
        "history_days": history_days,
        "horizon_days": horizon_days,
        "total_history": sum(per_day.values()),
        "daily": daily,
        "weekly": weeks,
        "by_weekday": [{"weekday": WEEKDAY_NAMES[i], "average": avg[i]} for i in range(7)],
        "by_service": sorted(
            ({"service_id": sid, **v} for sid, v in per_service.items()),
            key=lambda x: -x["count"],
        ),
        "forecast": forecast,
        "forecast_total": round(sum(f["expected"] for f in forecast), 1),
    }
