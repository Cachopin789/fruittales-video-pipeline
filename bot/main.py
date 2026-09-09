"""Punto de entrada del bot profesional FruitTales."""
import asyncio
from datetime import datetime
import logging
from time import monotonic
import discord
from discord.ext import commands, tasks
from config import load_settings
from embeds import channel_embed, help_embed, stats_embed, video_embed
from logging_setup import configure_logging
from programacion import next_scheduled_video
from schedule import is_due, is_notification_window, madrid_now
from server_setup import configure_server
from state import last_check, read, save
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
        super().__init__(command_prefix="!", intents=intents)
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
        if not is_due(last_check(), settings.check_interval_minutes, now): return
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
                channel = self.get_channel(settings.discord_channel_id) or await self.fetch_channel(settings.discord_channel_id)
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
        result = await configure_server(interaction.guild, interaction.guild.me)
        embed = discord.Embed(title="🍊 Servidor FruitTales configurado", color=0x2ECC71)
        embed.add_field(name="✅ Creados", value="\n".join(result.created) if result.created else "Nada: todo ya existía.", inline=False)
        embed.add_field(name="♻️ Ya existentes", value="\n".join(result.existing) if result.existing else "Ninguno.", inline=False)
        embed.add_field(name="🔔 Canal de avisos", value=f"<#{result.videos_channel_id}>", inline=False)
        embed.set_footer(text="Añade este ID a DISCORD_CHANNEL_ID si aún no está configurado.")
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info("Servidor %s configurado por el propietario.", interaction.guild.id)
    except discord.Forbidden:
        await interaction.followup.send("⚠️ Discord rechazó una acción. Revisa que mi rol esté por encima de los roles que debo gestionar.", ephemeral=True)
    except discord.DiscordException as error:
        logger.error("No se pudo configurar el servidor: %s", error)
        await interaction.followup.send("⚠️ No pude terminar la configuración. Revisa los permisos del bot e inténtalo de nuevo.", ephemeral=True)
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
    active = is_notification_window(now)
    embed = discord.Embed(title="🛡️ Estado de FruitTales Guardian", color=0x2ECC71 if active else 0xF39C12)
    embed.add_field(name="Monitor", value="🟢 En franja de avisos" if active else "🌙 En silencio programado", inline=True)
    embed.add_field(name="Hora de España", value=now.strftime("%H:%M · %d/%m/%Y"), inline=True)
    embed.add_field(name="Última comprobación", value=checked or "Aún no se ha realizado", inline=False)
    embed.add_field(name="Horario", value="YouTube se consulta solo entre **15:00 y 21:00** cada 30 minutos como máximo.", inline=False)
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
    logger.exception("Error ejecutando un comando: %s", error)
    text = "⚠️ Ha ocurrido un error temporal. Inténtalo de nuevo en unos segundos."
    if interaction.response.is_done(): await interaction.followup.send(text, ephemeral=True)
    else: await interaction.response.send_message(text, ephemeral=True)
if __name__ == "__main__": bot.run(settings.discord_token, log_handler=None, reconnect=True)
