"""Punto de entrada del bot profesional FruitTales."""
import asyncio
import logging
from time import monotonic
import discord
from discord.ext import commands, tasks
from config import load_settings
from embeds import stats_embed, video_embed
from logging_setup import configure_logging
from schedule import is_due, madrid_now
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
        super().__init__(command_prefix="!", intents=discord.Intents.default())
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
@bot.tree.command(name="ping", description="Comprueba la latencia actual del bot.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong · Latencia: **{round(bot.latency * 1000)} ms**", ephemeral=True)
@bot.tree.command(name="uptime", description="Muestra cuánto tiempo lleva encendido el bot.")
async def uptime(interaction: discord.Interaction):
    seconds = int(monotonic() - bot.started_at); hours, remainder = divmod(seconds, 3600); minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(f"🟢 En línea desde hace **{hours} h {minutes} min {seconds} s**.", ephemeral=True)
@bot.tree.command(name="ultimovideo", description="Muestra el último vídeo publicado.")
async def ultimovideo(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        video = await retry(bot.youtube.latest_video, "Consulta de /ultimovideo")
        await interaction.followup.send(embed=video_embed(video, "Último vídeo de FruitTalesES"))
    except YouTubeAPIError as error: await interaction.followup.send(f"⚠️ No pude consultar YouTube ahora mismo: {error}", ephemeral=True)
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
