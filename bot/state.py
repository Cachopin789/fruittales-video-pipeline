"""Estado local persistente y seguro del monitor de YouTube."""
import json
from datetime import datetime
from pathlib import Path
PATH = Path(__file__).with_name("state.json")

def read() -> dict:
    try: return json.loads(PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError): return {}

def last_check() -> datetime | None:
    value = read().get("last_check")
    try: return datetime.fromisoformat(value) if value else None
    except ValueError: return None

def notification_channel_id() -> int | None:
    """Devuelve el canal configurado por /configurar-servidor, si existe."""
    value = read().get("notification_channel_id")
    try: return int(value) if value else None
    except (TypeError, ValueError): return None

def save(*, video_id: str | None = None, checked_at: datetime | None = None, notification_channel: int | None = None) -> None:
    data = read()
    if video_id is not None: data["video_id"] = video_id
    if checked_at is not None: data["last_check"] = checked_at.isoformat()
    if notification_channel is not None: data["notification_channel_id"] = notification_channel
    temporary = PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(PATH)
