"""Punto de entrada del bot profesional FruitTales."""
import asyncio
from datetime import datetime
import logging
from time import monotonic
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot_config import notification_settings, read_config, save_config, time_to_minutes
from config import load_settings
from community import NUMBER_EMOJIS, find_text_channel, poll_embed, suggestion_embed
from embeds import channel_embed, help_embed, stats_embed, video_embed
from logging_setup import configure_logging
from management import find_category, normalize_channel_name, parse_colour
from programacion import next_scheduled_video
from schedule import is_due, is_notification_window, madrid_now
from server_setup import configure_server
from state import last_check, notification_channel_id, read, save
from youtube import YouTubeAPIError, YouTubeClient

configure_logging()
logger = logging.getLogger("fruittales")
settings = load_settings()

async def retry(operation, label: str, attempts: int = 3):
    """Reintenta operaciones de red transitorias con espera exponencial."""
    for attempt in range(1, attempts + 1):
        try: return await operation()
        except (YouTubeAPIError, discord.HTTPException, discord.GatewayNotFound, OSError) as error:
            if attempt == attempts: raise
            delay = 2 ** attempt
            logger.warning("%s falló (%s/%s): %s. Reintento en %ss.", label, attempt, attempts, error, delay)
            await asyncio.sleep(delay)

class FruitTalesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # Necesario para asignar el rol Miembro al entrar al servidor.
        # Solo usamos slash commands: evita pedir Message Content Intent innecesariamente.
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.youtube = YouTubeClient(settings.youtube_api_key, settings.youtube_channel_handle)
        self.started_at = monotonic()
    async def setup_hook(self):
        self.check_videos.start()
        await self.tree.sync()
        logger.info("Comandos de aplicación sincronizados.")
    async def on_ready(self): logger.info("Conectado como %s (ID: %s).", self.user, self.user.id if self.user else "?")
    async def on_disconnect(self): logger.warning("Discord desconectado; se intentará reconectar automáticamente.")
    async def on_app_command_completion(self, interaction, command):
        logger.info("Comando /%s usado por %s en servidor %s.", command.qualified_name, interaction.user.id, interaction.guild_id)
    async def on_member_join(self, member: discord.Member):
        """Da el rol de comunidad a miembros nuevos cuando el intent está habilitado."""
        role = discord.utils.get(member.guild.roles, name="Miembro")
        if role is None:
            return
        try:
            await member.add_roles(role, reason="Rol automático de bienvenida de FruitTales Guardian")
            logger.info("Rol Miembro asignado a %s.", member.id)
        except discord.DiscordException as error:
            logger.warning("No se pudo asignar Miembro a %s: %s", member.id, error)
    @tasks.loop(minutes=1)
    async def check_videos(self):
        """No consulta YouTube fuera de 15:00–21:00 (Europe/Madrid)."""
        now = madrid_now()
        interval, start, end = notification_settings()
        if not is_due(last_check(), interval, now, start, end): return
        save(checked_at=now)  # Evita gastar cuota reiteradamente durante una incidencia.
        logger.info("Comprobando YouTube a las %s (hora de España).", now.strftime("%H:%M"))
        try:
            video = await retry(self.youtube.latest_video, "Consulta a YouTube")
            previous_id = read().get("video_id")
            if previous_id is None:
                save(video_id=video.video_id); logger.info("Primer inicio: vídeo actual guardado sin anunciar."); return
            if previous_id == video.video_id:
                logger.info("No hay vídeo nuevo."); return
            async def send_notification():
                channel_id = read_config().get("notification_channel_id") or notification_channel_id() or settings.discord_channel_id
                channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                if not isinstance(channel, (discord.TextChannel, discord.Thread)):
                    raise discord.DiscordException("DISCORD_CHANNEL_ID no es un canal de texto.")
                await channel.send(embed=video_embed(video), allowed_mentions=discord.AllowedMentions.none())
            await retry(send_notification, "Envío de aviso a Discord")
            save(video_id=video.video_id); logger.info("Aviso enviado para el vídeo %s.", video.video_id)
        except (YouTubeAPIError, discord.DiscordException, OSError) as error:
            logger.error("No se pudo completar la comprobación: %s", error)
        except Exception: logger.exception("Error inesperado en el monitor de vídeos.")
    @check_videos.before_loop
    async def before_check_videos(self): await self.wait_until_ready()

bot = FruitTalesBot()
@bot.tree.command(name="configurar-servidor", description="Crea la estructura inicial del servidor FruitTales.")
async def configurar_servidor(interaction: discord.Interaction):
    """Comando de una sola persona: crea roles, categorías y canales sin duplicarlos."""
    if interaction.user.id != settings.owner_user_id:
        await interaction.response.send_message("🔒 Este comando está reservado para el propietario de FruitTales Guardian.", ephemeral=True)
        logger.warning("Intento no autorizado de /configurar-servidor por %s.", interaction.user.id)
        return
    if interaction.guild is None:
        await interaction.response.send_message("⚠️ Este comando solo se puede usar dentro de un servidor.", ephemeral=True)
        return
    if not interaction.guild.me or not interaction.guild.me.guild_permissions.administrator:
        await interaction.response.send_message("⚠️ Necesito el permiso **Administrador** para crear la estructura del servidor.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        result = await configure_server(interaction.guild, interaction.user, interaction.guild.me)
        save(notification_channel=result.videos_channel_id)
        save_config(notification_channel_id=result.videos_channel_id)
        embed = discord.Embed(title="🍊 Servidor FruitTales configurado", color=0x2ECC71)
        embed.add_field(name="✅ Creados", value="\n".join(result.created) if result.created else "Nada: todo ya existía.", inline=False)
        embed.add_field(name="✨ Migrados", value="\n".join(result.migrated) if result.migrated else "Ninguno.", inline=False)
        embed.add_field(name="♻️ Ya existentes", value="\n".join(result.existing) if result.existing else "Ninguno.", inline=False)
        embed.add_field(name="🔔 Canal de avisos", value=f"<#{result.videos_channel_id}>", inline=False)
        embed.set_footer(text="Este canal ya queda configurado para los avisos automáticos.")
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info("Servidor %s configurado por el propietario.", interaction.guild.id)
    except discord.Forbidden:
        await interaction.followup.send("⚠️ Discord rechazó una acción. Revisa que mi rol esté por encima de los roles que debo gestionar.", ephemeral=True)
    except discord.DiscordException as error:
        logger.error("No se pudo configurar el servidor: %s", error)
        await interaction.followup.send("⚠️ No pude terminar la configuración. Revisa los permisos del bot e inténtalo de nuevo.", ephemeral=True)


def _owner_guard(interaction: discord.Interaction) -> bool:
    return interaction.user.id == settings.owner_user_id


async def _private_owner_error(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("🔒 Este comando de gestión está reservado para el propietario de FruitTales Guardian.", ephemeral=True)
    logger.warning("Intento no autorizado de gestión por %s.", interaction.user.id)


@bot.tree.command(name="crear-canal", description="Crea un canal de texto o voz (solo propietario).")
@app_commands.describe(nombre="Nombre visible del canal", categoria="Nombre de la categoría", tipo="texto o voz")
async def crear_canal(interaction: discord.Interaction, nombre: str, categoria: str, tipo: Literal["texto", "voz"]):
    if not _owner_guard(interaction):
        await _private_owner_error(interaction); return
    if interaction.guild is None:
        await interaction.response.send_message("⚠️ Este comando solo funciona dentro de un servidor.", ephemeral=True); return
    category = find_category(interaction.guild, categoria)
    if category is None:
        await interaction.response.send_message("⚠️ No encuentro esa categoría. Escribe su nombre, por ejemplo `CONTENIDO` o `🤖 BOTS`.", ephemeral=True); return
    try:
        channel_name = normalize_channel_name(nombre)
    except ValueError as error:
        await interaction.response.send_message(f"⚠️ {error}", ephemeral=True); return
    collection = interaction.guild.text_channels if tipo == "texto" else interaction.guild.voice_channels
    if discord.utils.get(collection, name=channel_name):
        await interaction.response.send_message(f"ℹ️ Ya existe **{channel_name}**; no se creó un duplicado.", ephemeral=True); return
    try:
        if tipo == "texto":
            channel = await interaction.guild.create_text_channel(channel_name, category=category, reason="Creado por FruitTales Guardian")
        else:
            channel = await interaction.guild.create_voice_channel(channel_name, category=category, reason="Creado por FruitTales Guardian")
        await interaction.response.send_message(f"✅ Canal creado: {channel.mention} en **{category.name}**.", ephemeral=True)
    except discord.DiscordException as error:
        logger.error("No se pudo crear el canal: %s", error)
        await interaction.response.send_message("⚠️ No pude crear el canal. Revisa los permisos del bot.", ephemeral=True)


@bot.tree.command(name="crear-rol", description="Crea un rol con color (solo propietario).")
@app_commands.describe(nombre="Nombre del rol", color="Ejemplo: #E74C3C, rojo o verde")
async def crear_rol(interaction: discord.Interaction, nombre: str, color: str):
    if not _owner_guard(interaction):
        await _private_owner_error(interaction); return
    if interaction.guild is None:
        await interaction.response.send_message("⚠️ Este comando solo funciona dentro de un servidor.", ephemeral=True); return
    name = nombre.strip()[:100]
    if not name:
        await interaction.response.send_message("⚠️ Indica un nombre para el rol.", ephemeral=True); return
    if discord.utils.get(interaction.guild.roles, name=name):
        await interaction.response.send_message(f"ℹ️ El rol **{name}** ya existe; no se creó un duplicado.", ephemeral=True); return
    try:
        role = await interaction.guild.create_role(name=name, colour=parse_colour(color), reason="Creado por FruitTales Guardian")
        await interaction.response.send_message(f"✅ Rol creado: {role.mention}.", ephemeral=True)
    except ValueError as error:
        await interaction.response.send_message(f"⚠️ {error}", ephemeral=True)
    except discord.DiscordException as error:
        logger.error("No se pudo crear el rol: %s", error)
        await interaction.response.send_message("⚠️ No pude crear el rol. Revisa los permisos del bot.", ephemeral=True)


ajustes = app_commands.Group(name="ajustes", description="Consulta o cambia los ajustes del bot (solo propietario).")


@ajustes.command(name="ver", description="Muestra la configuración actual del bot.")
async def ajustes_ver(interaction: discord.Interaction):
    if not _owner_guard(interaction):
        await _private_owner_error(interaction); return
    config = read_config()
    channel_id = config.get("notification_channel_id") or notification_channel_id() or settings.discord_channel_id
    embed = discord.Embed(title="⚙️ Ajustes de FruitTales Guardian", color=0xE74C3C)
    embed.add_field(name="🔔 Canal de avisos", value=f"<#{channel_id}>" if channel_id else "Sin configurar", inline=False)
    embed.add_field(name="🕒 Horario (España)", value=f"{config['notification_start']}–{config['notification_end']}", inline=True)
    embed.add_field(name="⏱️ Intervalo", value=f"{max(30, int(config['check_interval_minutes']))} minutos", inline=True)
    embed.set_footer(text="Los secretos nunca se muestran en este comando.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@ajustes.command(name="cambiar-horario", description="Cambia la franja de comprobación de YouTube.")
@app_commands.describe(inicio="Hora inicial HH:MM, España", fin="Hora final HH:MM, España")
async def ajustes_cambiar_horario(interaction: discord.Interaction, inicio: str, fin: str):
    if not _owner_guard(interaction):
        await _private_owner_error(interaction); return
    try:
        if time_to_minutes(inicio) >= time_to_minutes(fin):
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin el mismo día.")
    except ValueError as error:
        await interaction.response.send_message(f"⚠️ {error}", ephemeral=True); return
    save_config(notification_start=inicio, notification_end=fin)
    await interaction.response.send_message(f"✅ Horario actualizado: **{inicio}–{fin}** (hora de España).", ephemeral=True)


@ajustes.command(name="cambiar-canal-avisos", description="Cambia el destino de los avisos de YouTube.")
async def ajustes_cambiar_canal_avisos(interaction: discord.Interaction, canal: discord.TextChannel):
    if not _owner_guard(interaction):
        await _private_owner_error(interaction); return
    save_config(notification_channel_id=canal.id)
    save(notification_channel=canal.id)
    await interaction.response.send_message(f"✅ Los próximos avisos se enviarán a {canal.mention}.", ephemeral=True)


bot.tree.add_command(ajustes)


@bot.tree.command(name="crear-invitacion", description="Genera una invitación del servidor (solo propietario).")
@app_commands.describe(duracion_horas="De 1 a 168 horas", usos_maximos="De 0 (sin límite) a 100")
async def crear_invitacion(interaction: discord.Interaction, duracion_horas: app_commands.Range[int, 1, 168], usos_maximos: app_commands.Range[int, 0, 100]):
    if not _owner_guard(interaction):
        await _private_owner_error(interaction); return
    if interaction.guild is None or not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("⚠️ Usa este comando desde un canal de texto del servidor.", ephemeral=True); return
    try:
        invite = await interaction.channel.create_invite(max_age=duracion_horas * 3600, max_uses=usos_maximos, unique=True, reason="Creada por FruitTales Guardian")
        uses = "sin límite" if usos_maximos == 0 else str(usos_maximos)
        await interaction.response.send_message(f"🔗 Invitación creada: {invite.url}\nCaduca en **{duracion_horas} h** y permite **{uses}** usos.", ephemeral=True)
    except discord.DiscordException as error:
        logger.error("No se pudo crear invitación: %s", error)
        await interaction.response.send_message("⚠️ No pude crear la invitación. Revisa el permiso **Crear invitación**.", ephemeral=True)
@bot.tree.command(name="ping", description="Comprueba la latencia actual del bot.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong · Latencia: **{round(bot.latency * 1000)} ms**", ephemeral=True)
@bot.tree.command(name="uptime", description="Muestra cuánto tiempo lleva encendido el bot.")
async def uptime(interaction: discord.Interaction):
    seconds = int(monotonic() - bot.started_at); hours, remainder = divmod(seconds, 3600); minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(f"🟢 En línea desde hace **{hours} h {minutes} min {seconds} s**.", ephemeral=True)
@bot.tree.command(name="ayuda", description="Muestra todos los comandos disponibles.")
async def ayuda(interaction: discord.Interaction):
    await interaction.response.send_message(embed=help_embed(), ephemeral=True)
@bot.tree.command(name="sugerir", description="Envía una idea o sugerencia para FruitTales.")
async def sugerir(interaction: discord.Interaction, idea: str):
    if interaction.guild is None:
        await interaction.response.send_message("⚠️ Las sugerencias solo se pueden enviar desde el servidor de FruitTales.", ephemeral=True)
        return
    idea = idea.strip()
    if len(idea) < 5 or len(idea) > 1000:
        await interaction.response.send_message("⚠️ Escribe una sugerencia de entre 5 y 1.000 caracteres.", ephemeral=True)
        return
    channel = None
    if settings.suggestions_channel_id:
        try:
            candidate = bot.get_channel(settings.suggestions_channel_id) or await bot.fetch_channel(settings.suggestions_channel_id)
            if isinstance(candidate, discord.TextChannel): channel = candidate
        except discord.DiscordException as error:
            logger.warning("SUGGESTIONS_CHANNEL_ID no está disponible: %s", error)
    channel = channel or find_text_channel(interaction.guild, "💡│sugerencias", "sugerencias")
    if channel is None:
        await interaction.response.send_message("⚠️ No encuentro el canal de sugerencias. Ejecuta `/configurar-servidor` o configura `SUGGESTIONS_CHANNEL_ID`.", ephemeral=True)
        return
    try:
        await channel.send(embed=suggestion_embed(interaction.user, idea), allowed_mentions=discord.AllowedMentions.none())
        await interaction.response.send_message("🍊 ¡Gracias! Tu sugerencia ya llegó al equipo de FruitTales.", ephemeral=True)
    except discord.DiscordException as error:
        logger.error("No se pudo enviar una sugerencia: %s", error)
        await interaction.response.send_message("⚠️ No pude enviar tu sugerencia ahora mismo. Inténtalo de nuevo más tarde.", ephemeral=True)
@bot.tree.command(name="encuesta", description="Crea una encuesta para la comunidad.")
async def encuesta(interaction: discord.Interaction, pregunta: str, opcion_1: str, opcion_2: str, opcion_3: str | None = None, opcion_4: str | None = None):
    if interaction.guild is None or not isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
        await interaction.response.send_message("⚠️ Las encuestas solo se pueden crear en un canal de texto del servidor.", ephemeral=True)
        return
    if interaction.user.id != settings.owner_user_id and not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("🔒 Solo el propietario o el equipo de moderación puede crear encuestas.", ephemeral=True)
        return
    options = [option.strip() for option in (opcion_1, opcion_2, opcion_3, opcion_4) if option and option.strip()]
    if len(pregunta.strip()) < 5 or len(pregunta) > 256 or len(options) < 2 or any(len(option) > 150 for option in options):
        await interaction.response.send_message("⚠️ Incluye al menos dos opciones y usa textos breves y claros.", ephemeral=True)
        return
    await interaction.response.send_message(embed=poll_embed(pregunta.strip(), options, interaction.user))
    message = await interaction.original_response()
    try:
        for emoji in NUMBER_EMOJIS[:len(options)]:
            await message.add_reaction(emoji)
    except discord.DiscordException as error:
        logger.warning("Encuesta creada sin todas las reacciones: %s", error)
@bot.tree.command(name="normas", description="Muestra dónde consultar las reglas del servidor.")
async def normas(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("⚠️ Este comando solo está disponible dentro del servidor.", ephemeral=True)
        return
    rules_channel = find_text_channel(interaction.guild, "📜│reglas", "reglas")
    if rules_channel:
        embed = discord.Embed(title="📜 Normas de FruitTales", description=f"Consulta las normas completas en {rules_channel.mention}. Gracias por mantener una comunidad amable y divertida.", color=0xE74C3C)
    else:
        embed = discord.Embed(title="📜 Normas de FruitTales", description="Aún no hay un canal de normas configurado. Un administrador puede crearlo con `/configurar-servidor`.", color=0xF39C12)
    await interaction.response.send_message(embed=embed, ephemeral=True)
@bot.tree.command(name="ultimovideo", description="Muestra el último vídeo publicado.")
async def ultimovideo(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        video = await retry(bot.youtube.latest_video, "Consulta de /ultimovideo")
        await interaction.followup.send(embed=video_embed(video, "Último vídeo de FruitTalesES"))
    except YouTubeAPIError as error: await interaction.followup.send(f"⚠️ No pude consultar YouTube ahora mismo: {error}", ephemeral=True)
@bot.tree.command(name="canal", description="Muestra información general de FruitTalesES.")
async def canal(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        info = await retry(bot.youtube.channel_info, "Consulta de /canal")
        await interaction.followup.send(embed=channel_embed(info))
    except YouTubeAPIError as error: await interaction.followup.send(f"⚠️ No pude consultar el canal ahora mismo: {error}", ephemeral=True)
@bot.tree.command(name="random", description="Recomienda un vídeo aleatorio de FruitTalesES.")
async def random_video(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        video = await retry(bot.youtube.random_video, "Consulta de /random")
        await interaction.followup.send(embed=video_embed(video, "🎲 Recomendación aleatoria de FruitTalesES"))
    except YouTubeAPIError as error: await interaction.followup.send(f"⚠️ No pude elegir un vídeo ahora mismo: {error}", ephemeral=True)
@bot.tree.command(name="proximo", description="Muestra el próximo vídeo anunciado.")
async def proximo(interaction: discord.Interaction):
    scheduled = next_scheduled_video()
    if scheduled:
        moment = scheduled.published_at
        title = scheduled.title
        url = scheduled.url
    elif settings.next_video_at:
        try:
            moment = datetime.fromisoformat(settings.next_video_at)
            if moment.tzinfo is None: moment = moment.replace(tzinfo=madrid_now().tzinfo)
            title = settings.next_video_title or "Próxima aventura de FruitTales"
            url = settings.next_video_url
            if moment <= madrid_now():
                await interaction.response.send_message("🍊 No hay más publicaciones futuras en el calendario por ahora. Añade la siguiente a `programacion.json`.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("⚠️ La fecha configurada para el próximo vídeo no tiene un formato válido. Usa `AAAA-MM-DDTHH:MM`.", ephemeral=True)
            return
    else:
        await interaction.response.send_message("🍊 Aún no hay una próxima publicación programada. Vuelve pronto para descubrir la siguiente historia.", ephemeral=True)
        return
    try:
        embed = discord.Embed(title="📅 Próximo vídeo de FruitTalesES", color=0xE74C3C, timestamp=moment)
        embed.add_field(name="🎬 Título", value=title, inline=False)
        embed.add_field(name="🕒 Hora de España", value=moment.strftime("%d/%m/%Y · %H:%M"), inline=True)
        if url: embed.add_field(name="🔗 Enlace", value=f"[Ver programación]({url})", inline=True)
        embed.set_footer(text="Información configurada por el equipo de FruitTales")
        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message("⚠️ La fecha configurada para el próximo vídeo no tiene un formato válido. Usa `AAAA-MM-DDTHH:MM`.", ephemeral=True)
@bot.tree.command(name="estado", description="Muestra el estado del monitor de avisos.")
async def estado(interaction: discord.Interaction):
    now = madrid_now(); state = read(); checked = state.get("last_check")
    interval, start, end = notification_settings()
    active = is_notification_window(now, start, end)
    horario = f"{start // 60:02d}:{start % 60:02d}–{end // 60:02d}:{end % 60:02d}"
    embed = discord.Embed(title="🛡️ Estado de FruitTales Guardian", color=0x2ECC71 if active else 0xF39C12)
    embed.add_field(name="Monitor", value="🟢 En franja de avisos" if active else "🌙 En silencio programado", inline=True)
    embed.add_field(name="Hora de España", value=now.strftime("%H:%M · %d/%m/%Y"), inline=True)
    embed.add_field(name="Última comprobación", value=checked or "Aún no se ha realizado", inline=False)
    embed.add_field(name="Horario", value=f"YouTube se consulta solo entre **{horario}** cada **{interval} minutos** como máximo.", inline=False)
    embed.set_footer(text="🍊 FruitTales Guardian · Monitor de YouTube")
    await interaction.response.send_message(embed=embed, ephemeral=True)
@bot.tree.command(name="stats", description="Muestra estadísticas actuales de FruitTalesES.")
async def stats(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        title, subscribers, videos, views = await retry(bot.youtube.stats, "Consulta de /stats")
        await interaction.followup.send(embed=stats_embed(title, subscribers, videos, views))
    except YouTubeAPIError as error: await interaction.followup.send(f"⚠️ No pude consultar YouTube ahora mismo: {error}", ephemeral=True)
@bot.tree.error
async def command_error(interaction: discord.Interaction, error):
    logger.error("Error ejecutando un comando: %s", error, exc_info=(type(error), error, error.__traceback__))
    text = "⚠️ Ha ocurrido un error temporal. Inténtalo de nuevo en unos segundos."
    if interaction.response.is_done(): await interaction.followup.send(text, ephemeral=True)
    else: await interaction.response.send_message(text, ephemeral=True)
if __name__ == "__main__": bot.run(settings.discord_token, log_handler=None, reconnect=True)
