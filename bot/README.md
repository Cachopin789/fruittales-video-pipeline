# FruitTales Bot

Bot profesional e independiente del pipeline de vídeo. Envía avisos de nuevos vídeos de `FruitTalesES` y ofrece `/stats`, `/ultimovideo`, `/ping` y `/uptime`.

## Horario de avisos

El monitor usa siempre la hora local de España (`Europe/Madrid`):

- Entre **15:00 y 21:00**, consulta YouTube como máximo una vez cada 30 minutos y anuncia un vídeo nuevo si existe.
- Entre **21:00 y 15:00 del día siguiente**, no consulta la API de YouTube ni envía avisos.
- Aunque `CHECK_INTERVAL_MINUTES` tuviera un valor menor en `.env`, el bot lo limita automáticamente a 30 minutos para proteger la cuota.

Los comandos manuales siguen disponibles mientras el bot esté conectado. En su primer inicio guarda el último vídeo sin anunciarlo para no publicar una alerta antigua.

## Ejecutarlo en tu PC

Necesitas Python 3.11 o superior. En una terminal abierta dentro de `bot/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Completa antes `bot/.env` y guárdalo. Nunca compartas el token o la API key ni subas `.env` a GitHub.

## Discord

1. Crea una aplicación en [Discord Developer Portal](https://discord.com/developers/applications) y agrega un bot.
2. En **Bot**, genera el token y guárdalo en `DISCORD_TOKEN`.
3. En **OAuth2 > URL Generator**, marca `bot` y `applications.commands`.
4. Concede **View Channels**, **Send Messages**, **Embed Links** y **Read Message History**; abre el enlace para invitarlo.
5. Activa el modo desarrollador de Discord, usa clic derecho sobre el canal de avisos > **Copiar ID** y guárdalo en `DISCORD_CHANNEL_ID`.

## API de YouTube

En [Google Cloud Console](https://console.cloud.google.com/), crea un proyecto, habilita **YouTube Data API v3** y crea una **Clave de API** en **APIs y servicios > Credenciales**. Restringe la clave a YouTube Data API v3 y guárdala en `YOUTUBE_API_KEY`. Solo se consultan datos públicos: OAuth de YouTube no es necesario.

## Logs y solución de problemas

El bot registra su actividad tanto en la consola como en `bot/logs/bot.log`. Conserva hasta cinco archivos de 2 MB; allí verás arranques, reconexiones, consultas, avisos, reintentos y uso de comandos.

- Si no aparecen los comandos `/`, espera unos minutos tras invitarlo o reinícialo.
- Si no envía avisos, confirma el ID y que tenga permisos en el canal.
- Si falla YouTube, confirma que la API está habilitada y que la API key es correcta.

## Hosting 24/7: Railway o Render

No subas `.env`; crea sus variables como secretos en la plataforma. Los planes gratuitos y sus límites cambian, así que consulta las condiciones vigentes.

- **Railway:** conecta el repositorio, usa `bot` como **Root Directory**, añade las variables y arranca con `python main.py`.
- **Render:** crea un **Background Worker**, usa `bot` como directorio raíz, `pip install -r requirements.txt` como build command y `python main.py` como start command.

Un bot requiere un worker persistente; si un plan gratuito suspende workers, no podrá mantenerse conectado 24/7.
