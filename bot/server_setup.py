"""Creación idempotente de la estructura inicial del servidor FruitTales."""
from dataclasses import dataclass
import discord

@dataclass
class SetupResult:
    created: list[str]
    existing: list[str]
    videos_channel_id: int

async def _category(guild: discord.Guild, name: str, result: SetupResult) -> discord.CategoryChannel:
    found = discord.utils.get(guild.categories, name=name)
    if found:
        result.existing.append(name)
        return found
    channel = await guild.create_category(name, reason="Configuración inicial de FruitTales Guardian")
    result.created.append(name)
    return channel

async def _text_channel(guild: discord.Guild, category: discord.CategoryChannel, name: str, result: SetupResult, overwrites=None) -> discord.TextChannel:
    found = discord.utils.get(guild.text_channels, name=name)
    if found:
        if overwrites is not None:
            await found.edit(overwrites=overwrites, reason="Ajuste de permisos de FruitTales Guardian")
        result.existing.append(f"#{name}")
        return found
    channel = await guild.create_text_channel(name, category=category, overwrites=overwrites, reason="Configuración inicial de FruitTales Guardian")
    result.created.append(f"#{name}")
    return channel

async def _voice_channel(guild: discord.Guild, category: discord.CategoryChannel, name: str, result: SetupResult) -> discord.VoiceChannel:
    found = discord.utils.get(guild.voice_channels, name=name)
    if found:
        result.existing.append(f"🔊 {name}")
        return found
    channel = await guild.create_voice_channel(name, category=category, reason="Configuración inicial de FruitTales Guardian")
    result.created.append(f"🔊 {name}")
    return channel

async def _role(guild: discord.Guild, name: str, colour: discord.Colour, result: SetupResult) -> discord.Role:
    found = discord.utils.get(guild.roles, name=name)
    if found:
        result.existing.append(f"Rol {name}")
        return found
    role = await guild.create_role(name=name, colour=colour, reason="Configuración inicial de FruitTales Guardian")
    result.created.append(f"Rol {name}")
    return role

async def configure_server(guild: discord.Guild, bot_member: discord.Member) -> SetupResult:
    """Crea solo los elementos ausentes y devuelve un resumen para el propietario."""
    result = SetupResult([], [], 0)
    admin_role = await _role(guild, "Admin", discord.Colour.red(), result)
    await _role(guild, "Miembro", discord.Colour.green(), result)

    information = await _category(guild, "📢 INFORMACIÓN", result)
    content = await _category(guild, "🎬 CONTENIDO", result)
    community = await _category(guild, "💬 COMUNIDAD", result)
    voice = await _category(guild, "🎙️ VOZ", result)

    # Solo el rol Admin y el bot pueden escribir anuncios; todos pueden leerlos.
    announcement_overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
        admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }
    await _text_channel(guild, information, "anuncios", result, announcement_overwrites)
    await _text_channel(guild, information, "reglas", result)
    await _text_channel(guild, information, "enlaces-canal", result)
    videos = await _text_channel(guild, content, "nuevos-videos", result)
    await _text_channel(guild, content, "sugerencias", result)
    await _text_channel(guild, community, "general", result)
    await _text_channel(guild, community, "memes-frutales", result)
    await _voice_channel(guild, voice, "Sala general", result)
    result.videos_channel_id = videos.id
    return result
