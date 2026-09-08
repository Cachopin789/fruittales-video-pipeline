"""Logging en consola y en un archivo rotativo para diagnosticar el bot."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging() -> None:
    log_dir = Path(__file__).with_name("logs")
    log_dir.mkdir(exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(log_dir / "bot.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[console, file_handler], force=True)
