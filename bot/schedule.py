"""Reglas horarias de avisos usando siempre la zona local de España."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SPAIN_TIMEZONE = ZoneInfo("Europe/Madrid")
ALLOWED_START_HOUR = 15
ALLOWED_END_HOUR = 21

def madrid_now() -> datetime:
    return datetime.now(SPAIN_TIMEZONE)

def is_notification_window(now: datetime | None = None) -> bool:
    """Devuelve True solo entre las 15:00 (incluida) y las 21:00 (excluida)."""
    now = now or madrid_now()
    return ALLOWED_START_HOUR <= now.hour < ALLOWED_END_HOUR

def is_due(last_check: datetime | None, interval_minutes: int, now: datetime | None = None) -> bool:
    """Evita peticiones fuera de horario y antes del intervalo configurado."""
    now = now or madrid_now()
    return is_notification_window(now) and (last_check is None or now - last_check >= timedelta(minutes=interval_minutes))
