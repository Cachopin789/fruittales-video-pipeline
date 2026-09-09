"""Utilidades para los comandos privados de administración del servidor."""
import re
import discord

CHANNEL_ICON = "🧩│"


def owner_only(interaction: discord.Interaction, owner_id: int) -> bool:
    return interaction.user.id == owner_id


def normalize_channel_name(name: str) -> str:
    """Genera un nombre legible, consistente y válido para un canal de Discord."""
    clean = re.sub(r"\s+", "-", name.strip().lower())
    clean = re.sub(r"[^\w\-áéíóúüñ]", "", clean, flags=re.IGNORECASE).strip("-")
    if not clean:
        raise ValueError("El nombre debe incluir letras o números.")
    return f"{CHANNEL_ICON}{clean}"[:100]


def find_category(guild: discord.Guild, requested: str) -> discord.CategoryChannel | None:
    """Busca categorías por nombre completo o por una parte sin emoji."""
    wanted = requested.casefold().strip()
    for category in guild.categories:
        normalized = category.name.casefold().replace("📢", "").replace("🎬", "").replace("💬", "").replace("🎙️", "").replace("🤖", "").strip()
        if category.name.casefold() == wanted or normalized == wanted:
            return category
    return None


def parse_colour(value: str) -> discord.Colour:
    """Acepta #RRGGBB o nombres comunes, sin depender de entradas inseguras."""
    named = {
        "rojo": discord.Colour.red(), "verde": discord.Colour.green(), "azul": discord.Colour.blue(),
        "amarillo": discord.Colour.gold(), "naranja": discord.Colour.orange(), "morado": discord.Colour.purple(),
        "rosa": discord.Colour.magenta(), "gris": discord.Colour.light_grey(),
    }
    if value.casefold().strip() in named:
        return named[value.casefold().strip()]
    raw = value.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", raw):
        raise ValueError("Usa un color como `#E74C3C` o un nombre: rojo, verde, azul, naranja, morado, rosa o gris.")
    return discord.Colour(int(raw, 16))
