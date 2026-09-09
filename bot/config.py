"""Configuracion privada leida desde .env."""
from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    discord_token: str
    youtube_api_key: str
    owner_user_id: int
    discord_channel_id: int
    youtube_channel_handle: str
    check_interval_minutes: int
    next_video_at: str | None
    next_video_title: str | None
    next_video_url: str | None
    suggestions_channel_id: int | None

def load_settings() -> Settings:
    # Carga siempre el .env junto a este archivo, aunque se inicie desde la raíz.
    load_dotenv(Path(__file__).with_name(".env"))
    missing = [key for key in ("DISCORD_TOKEN", "YOUTUBE_API_KEY", "DISCORD_CHANNEL_ID", "OWNER_USER_ID") if not os.getenv(key)]
    if missing:
        raise RuntimeError("Faltan valores en .env: " + ", ".join(missing))
    try:
        requested_interval = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
        suggestion_channel = os.getenv("SUGGESTIONS_CHANNEL_ID")
        # El requisito del proyecto prohíbe consultas más frecuentes de 30 minutos.
        safe_interval = max(30, requested_interval)
        return Settings(
            os.environ["DISCORD_TOKEN"], os.environ["YOUTUBE_API_KEY"], int(os.environ["OWNER_USER_ID"]),
            int(os.environ["DISCORD_CHANNEL_ID"]), os.getenv("YOUTUBE_CHANNEL_HANDLE", "FruitTalesES").lstrip("@"),
            safe_interval, os.getenv("NEXT_VIDEO_AT") or None, os.getenv("NEXT_VIDEO_TITLE") or None,
            os.getenv("NEXT_VIDEO_URL") or None, int(suggestion_channel) if suggestion_channel else None,
        )
    except ValueError as error:
        raise RuntimeError("DISCORD_CHANNEL_ID y CHECK_INTERVAL_MINUTES deben ser numeros.") from error
