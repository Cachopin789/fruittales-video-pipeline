"""Lectura del calendario público de próximas publicaciones de FruitTales."""
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from schedule import SPAIN_TIMEZONE, madrid_now

SCHEDULE_FILE = Path(__file__).with_name("programacion.json")

@dataclass(frozen=True)
class ScheduledVideo:
    title: str
    published_at: datetime
    url: str | None = None

def next_scheduled_video(now: datetime | None = None) -> ScheduledVideo | None:
    """Devuelve el primer vídeo futuro del calendario, siempre en hora de España."""
    now = now or madrid_now()
    try:
        entries = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    videos = []
    for entry in entries:
        try:
            moment = datetime.fromisoformat(entry["published_at"])
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=SPAIN_TIMEZONE)
            videos.append(ScheduledVideo(entry["title"], moment, entry.get("url") or None))
        except (KeyError, TypeError, ValueError):
            continue
    return next((video for video in sorted(videos, key=lambda item: item.published_at) if video.published_at > now), None)
