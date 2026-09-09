"""Embeds coherentes y legibles para los mensajes de Discord."""
from datetime import datetime
import discord
from youtube import ChannelInfo, Video

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

def channel_embed(channel: ChannelInfo) -> discord.Embed:
    description = channel.description[:900] + ("…" if len(channel.description) > 900 else "")
    embed = discord.Embed(title=f"🍊 {channel.title}", description=description, url=channel.url, color=BRAND_RED)
    embed.add_field(name="🔗 Enlace", value=f"[Visitar canal]({channel.url})", inline=True)
    if channel.published_at: embed.add_field(name="📅 Creado", value=channel.published_at[:10], inline=True)
    if channel.thumbnail_url: embed.set_thumbnail(url=channel.thumbnail_url)
    embed.set_footer(text="Información pública de YouTube")
    return embed

def help_embed() -> discord.Embed:
    embed = discord.Embed(title="🍊 FruitTales Guardian · Ayuda", description="Tu compañero para seguir el canal FruitTalesES.", color=BRAND_RED)
    embed.add_field(name="📺 Canal", value="`/canal` · información general\n`/stats` · estadísticas actuales\n`/ultimovideo` · último vídeo\n`/random` · recomendación aleatoria", inline=False)
    embed.add_field(name="🔔 Seguimiento", value="`/proximo` · próxima publicación anunciada\n`/estado` · estado del monitor y horario", inline=False)
    embed.add_field(name="🛠️ Bot", value="`/ping` · latencia\n`/uptime` · tiempo en línea\n`/ayuda` · esta guía\n`/configurar-servidor` · estructura inicial (solo propietario)", inline=False)
    embed.set_footer(text="Los avisos automáticos se envían entre 15:00 y 21:00, hora de España.")
    return embed
