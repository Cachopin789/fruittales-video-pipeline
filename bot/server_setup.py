"""Creación idempotente de la estructura y privacidad del servidor FruitTales."""
from dataclasses import dataclass
import discord


@dataclass
class SetupResult:
    created: list[str]
    existing: list[str]
    migrated: list[str]
    videos_channel_id: int


async def _role(guild: discord.Guild, name: str, colour: discord.Colour, result: SetupResult) -> discord.Role:
    role = discord.utils.get(guild.roles, name=name)
    if role:
        result.existing.append(f"Rol {name}")
        return role
    role = await guild.create_role(name=name, colour=colour, reason="Configuración inicial de FruitTales Guardian")
    result.created.append(f"Rol {name}")
    return role


async def _category(guild: discord.Guild, name: str, overwrites: dict, result: SetupResult) -> discord.CategoryChannel:
    category = discord.utils.get(guild.categories, name=name)
    if category:
        await category.edit(overwrites=overwrites, reason="Privacidad de FruitTales Guardian")
        result.existing.append(name)
        return category
    category = await guild.create_category(name, overwrites=overwrites, reason="Configuración inicial de FruitTales Guardian")
    result.created.append(name)
    return category


async def _text_channel(guild: discord.Guild, category: discord.CategoryChannel, name: str, result: SetupResult, *, legacy_names: tuple[str, ...] = (), overwrites: dict | None = None) -> discord.TextChannel:
    channel = discord.utils.get(guild.text_channels, name=name)
    legacy_name = None
    if channel is None:
        for old_name in legacy_names:
            channel = discord.utils.get(guild.text_channels, name=old_name)
            if channel:
                legacy_name = old_name
                break
    if channel:
        changes: dict = {}
        if legacy_name: changes["name"] = name
        if channel.category_id != category.id: changes["category"] = category
        if overwrites is not None: changes["overwrites"] = overwrites
        if changes: await channel.edit(**changes, reason="Migración y privacidad de FruitTales Guardian")
        (result.migrated if legacy_name else result.existing).append(f"#{legacy_name} → #{name}" if legacy_name else f"#{name}")
        return channel
    options = {"category": category, "reason": "Configuración inicial de FruitTales Guardian"}
    if overwrites is not None: options["overwrites"] = overwrites
    channel = await guild.create_text_channel(name, **options)
    result.created.append(f"#{name}")
    return channel


async def _voice_channel(guild: discord.Guild, category: discord.CategoryChannel, name: str, result: SetupResult, *, legacy_names: tuple[str, ...] = (), overwrites: dict | None = None) -> discord.VoiceChannel:
    channel = discord.utils.get(guild.voice_channels, name=name)
    legacy_name = None
    if channel is None:
        for old_name in legacy_names:
            channel = discord.utils.get(guild.voice_channels, name=old_name)
            if channel:
                legacy_name = old_name
                break
    if channel:
        changes: dict = {}
        if legacy_name: changes["name"] = name
        if channel.category_id != category.id: changes["category"] = category
        if overwrites is not None: changes["overwrites"] = overwrites
        if changes: await channel.edit(**changes, reason="Migración y privacidad de FruitTales Guardian")
        (result.migrated if legacy_name else result.existing).append(name)
        return channel
    options = {"category": category, "reason": "Configuración inicial de FruitTales Guardian"}
    if overwrites is not None: options["overwrites"] = overwrites
    channel = await guild.create_voice_channel(name, **options)
    result.created.append(name)
    return channel


def _private_overwrites(guild: discord.Guild, owner: discord.Member, bot_member: discord.Member, bots_role: discord.Role) -> dict:
    """Privado para personas; abierto al propietario y al rol que se da a bots futuros."""
    allow = discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)
    return {guild.default_role: discord.PermissionOverwrite(view_channel=False), owner: allow, bot_member: allow, bots_role: allow}


def _public_overwrites(guild: discord.Guild, bot_member: discord.Member, bots_role: discord.Role) -> dict:
    allow = discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)
    return {guild.default_role: allow, bot_member: allow, bots_role: allow}


async def configure_server(guild: discord.Guild, owner: discord.Member, bot_member: discord.Member) -> SetupResult:
    """Crea o migra la estructura, incluida la privacidad, sin duplicar recursos."""
    result = SetupResult([], [], [], 0)
    await _role(guild, "Admin", discord.Colour.red(), result)
    await _role(guild, "Miembro", discord.Colour.green(), result)
    bots_role = await _role(guild, "Bots", discord.Colour.dark_teal(), result)
    private = _private_overwrites(guild, owner, bot_member, bots_role)
    public = _public_overwrites(guild, bot_member, bots_role)
    information = await _category(guild, "📢 INFORMACIÓN", private, result)
    content = await _category(guild, "🎬 CONTENIDO", private, result)
    community = await _category(guild, "💬 COMUNIDAD", private, result)
    voice = await _category(guild, "🎙️ VOZ", private, result)
    bots = await _category(guild, "🤖 BOTS", private, result)
    await _text_channel(guild, information, "📌│anuncios", result, legacy_names=("anuncios",), overwrites=private)
    await _text_channel(guild, information, "📜│reglas", result, legacy_names=("reglas",), overwrites=private)
    await _text_channel(guild, information, "🔗│enlaces-canal", result, legacy_names=("enlaces-canal",), overwrites=private)
    await _text_channel(guild, bots, "🤖│bot-comandos", result, legacy_names=("bot-comandos",), overwrites=private)
    videos = await _text_channel(guild, content, "🔔│nuevos-videos", result, legacy_names=("nuevos-videos",), overwrites=public)
    await _text_channel(guild, content, "💡│sugerencias", result, legacy_names=("sugerencias",), overwrites=private)
    await _text_channel(guild, community, "💬│general", result, legacy_names=("general",), overwrites=public)
    await _text_channel(guild, community, "🍊│memes-frutales", result, legacy_names=("memes-frutales",), overwrites=private)
    await _voice_channel(guild, voice, "🔊 Sala general", result, legacy_names=("Sala general",), overwrites=private)
    result.videos_channel_id = videos.id
    return result
