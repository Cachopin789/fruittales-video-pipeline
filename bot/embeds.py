"""Embeds coherentes y legibles para los mensajes de Discord."""
from datetime import datetime
import discord
from youtube import Video

BRAND_RED = 0xE74C3C

def video_embed(video: Video, heading: str = "Nuevo vídeo de FruitTalesES") -> discord.Embed:
    embed = discord.Embed(title=heading, description=f"## [{video.title}]({video.url})", url=video.url, color=BRAND_RED)
    embed.add_field(name="▶ Ver en YouTube", value=f"[Abrir vídeo]({video.url})", inline=True)
    embed.add_field(name="Canal", value="FruitTalesES", inline=True)
    if video.published_at:
        try:
            published = datetime.fromisoformat(video.published_at.replace("Z", "+00:00"))
            embed.timestamp = published
        except ValueError:
            pass
    if video.thumbnail_url:
        embed.set_image(url=video.thumbnail_url)
    embed.set_footer(text="FruitTales Bot · Avisos de YouTube")
    return embed

def stats_embed(title: str, subscribers: int | None, videos: int, views: int) -> discord.Embed:
    embed = discord.Embed(title=f"📊 Estadísticas de {title}", color=BRAND_RED)
    embed.add_field(name="👥 Suscriptores", value=f"{subscribers:,}" if subscribers is not None else "Ocultos", inline=True)
    embed.add_field(name="🎬 Vídeos", value=f"{videos:,}", inline=True)
    embed.add_field(name="👁️ Visualizaciones", value=f"{views:,}", inline=True)
    embed.set_footer(text="Datos obtenidos de YouTube Data API v3")
    return embed
