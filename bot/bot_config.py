"""Configuración editable del bot que se conserva entre reinicios.

No guarda tokens ni claves: esos secretos siguen exclusivamente en ``.env``.
"""
import json
from pathlib import Path

PATH = Path(__file__).with_name("config_bot.json")
DEFAULTS = {
    "check_interval_minutes": 30,
    "notification_start": "15:00",
    "notification_end": "21:00",
    "notification_channel_id": None,
}


def read_config() -> dict:
    """Lee la configuración local y completa valores ausentes con valores seguros."""
    try:
        content = json.loads(PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        content = {}
    return DEFAULTS | {key: content[key] for key in DEFAULTS if key in content}


def save_config(**changes: object) -> dict:
    """Guarda cambios de manera atómica para no dañar el archivo ante un corte."""
    config = read_config()
    config.update(changes)
    temporary = PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(PATH)
    return config


def time_to_minutes(value: str) -> int:
    """Convierte HH:MM a minutos y rechaza horarios inválidos."""
    try:
        hours, minutes = (int(part) for part in value.split(":"))
    except (ValueError, AttributeError):
        raise ValueError("Usa el formato HH:MM, por ejemplo 15:00.") from None
    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        raise ValueError("La hora debe estar entre 00:00 y 23:59.")
    return hours * 60 + minutes


def notification_settings() -> tuple[int, int, int]:
    """Devuelve intervalo y franja; nunca permite menos de 30 minutos."""
    config = read_config()
    try:
        interval = max(30, int(config["check_interval_minutes"]))
        start = time_to_minutes(str(config["notification_start"]))
        end = time_to_minutes(str(config["notification_end"]))
    except (KeyError, TypeError, ValueError):
        return 30, 15 * 60, 21 * 60
    if start >= end:
        return interval, 15 * 60, 21 * 60
    return interval, start, end
