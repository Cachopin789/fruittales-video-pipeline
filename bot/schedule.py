"""Reglas horarias de avisos usando siempre la zona local de España."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SPAIN_TIMEZONE = ZoneInfo("Europe/Madrid")
ALLOWED_START_HOUR = 15
ALLOWED_END_HOUR = 21

def madrid_now() -> datetime:
    return datetime.now(SPAIN_TIMEZONE)

def is_notification_window(now: datetime | None = None, start_minutes: int = 15 * 60, end_minutes: int = 21 * 60) -> bool:
    """Devuelve True dentro de la franja local configurada, con final excluido."""
    now = now or madrid_now()
    current_minutes = now.hour * 60 + now.minute
    return start_minutes <= current_minutes < end_minutes

def is_due(last_check: datetime | None, interval_minutes: int, now: datetime | None = None, start_minutes: int = 15 * 60, end_minutes: int = 21 * 60) -> bool:
    """Evita peticiones fuera de horario y antes del intervalo configurado."""
    now = now or madrid_now()
    return is_notification_window(now, start_minutes, end_minutes) and (last_check is None or now - last_check >= timedelta(minutes=interval_minutes))
