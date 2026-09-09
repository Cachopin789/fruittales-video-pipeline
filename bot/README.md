# FruitTales Bot

**FruitTales Guardian** es un bot profesional e independiente del pipeline de vídeo. Envía avisos de nuevos vídeos de `FruitTalesES`, consulta información pública del canal y acompaña a la comunidad con comandos útiles.

## 🍊 Comandos

| Comando | Para qué sirve |
| :-- | :-- |
| `/ayuda` | Muestra la guía de comandos en Discord. |
| `/canal` | Enseña datos generales del canal de YouTube. |
| `/stats` | Muestra suscriptores, vídeos y visualizaciones. |
| `/ultimovideo` | Comparte el último vídeo publicado. |
| `/random` | Recomienda un vídeo aleatorio entre los 50 más recientes. |
| `/proximo` | Muestra la próxima publicación anunciada. |
| `/estado` | Indica el estado y horario del monitor. |
| `/configurar-servidor` | Crea una estructura profesional de canales y roles una sola vez. |
| `/ping` y `/uptime` | Comprueban latencia y tiempo en línea. |

Hay una explicación y ejemplo de cada comando en [`comandos-docs/`](comandos-docs/).

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

Para proteger el comando de configuración inicial, añade tu ID numérico de Discord:

```env
OWNER_USER_ID=1135502107106086932
```

`/proximo` usa primero [`programacion.json`](programacion.json): selecciona automáticamente la primera publicación futura y cambia a la siguiente al pasar su fecha. Para añadir una nueva, agrega un bloque con título, fecha `AAAA-MM-DDTHH:MM` (hora de España) y enlace opcional. Las variables siguientes siguen disponibles como alternativa si no existe un calendario:

```env
NEXT_VIDEO_AT=2026-09-10T18:00
NEXT_VIDEO_TITLE=La próxima aventura de FruitTales
NEXT_VIDEO_URL=https://www.youtube.com/@FruitTalesES
```

## Discord

1. Crea una aplicación en [Discord Developer Portal](https://discord.com/developers/applications) y agrega un bot.
2. En **Bot**, genera el token y guárdalo en `DISCORD_TOKEN`.
3. En **OAuth2 > URL Generator**, marca `bot` y `applications.commands`.
4. Concede **View Channels**, **Send Messages**, **Embed Links** y **Read Message History**; abre el enlace para invitarlo.
5. Activa el modo desarrollador de Discord, usa clic derecho sobre el canal de avisos > **Copiar ID** y guárdalo en `DISCORD_CHANNEL_ID`.
6. En **Bot > Privileged Gateway Intents**, activa **Server Members Intent**. Así FruitTales Guardian podrá asignar el rol `Miembro` a quienes entren al servidor.

## 🏗️ Configurar el servidor por primera vez

1. Da al bot el permiso **Administrador** y asegúrate de que su rol esté por encima de los roles que debe gestionar.
2. Comprueba que `OWNER_USER_ID` contiene tu ID numérico de Discord.
3. En tu servidor, ejecuta `/configurar-servidor` una sola vez.
4. El bot creará, sin duplicar lo existente, las categorías `📢 INFORMACIÓN`, `🎬 CONTENIDO`, `💬 COMUNIDAD` y `🎙️ VOZ`; sus canales, la sala de voz y los roles `Admin` y `Miembro`.
5. Copia el ID de `#nuevos-videos` mostrado en la confirmación y úsalo como `DISCORD_CHANNEL_ID` en `.env` si todavía no estaba configurado. Reinicia el bot después de cambiarlo.

El comando es privado y solo responde al usuario configurado en `OWNER_USER_ID`. Las personas que se unan después recibirán automáticamente el rol `Miembro`.

## API de YouTube

En [Google Cloud Console](https://console.cloud.google.com/), crea un proyecto, habilita **YouTube Data API v3** y crea una **Clave de API** en **APIs y servicios > Credenciales**. Restringe la clave a YouTube Data API v3 y guárdala en `YOUTUBE_API_KEY`. Solo se consultan datos públicos: OAuth de YouTube no es necesario.

## Logs y solución de problemas

El bot registra su actividad tanto en la consola como en `bot/logs/bot.log`. Conserva hasta cinco archivos de 2 MB; allí verás arranques, reconexiones, consultas, avisos, reintentos y uso de comandos.

- Si no aparecen los comandos `/`, espera unos minutos tras invitarlo o reinícialo.
- Si no envía avisos, confirma el ID y que tenga permisos en el canal.
- Si falla YouTube, confirma que la API está habilitada y que la API key es correcta.

## 🚀 Hosting 24/7 con Railway

Recomiendo **Railway** por ser la opción más directa para principiantes: conecta el repositorio, instala dependencias y ejecuta el bot. Un bot necesita un proceso persistente; los créditos y planes gratuitos cambian con el tiempo, así que revisa las condiciones de Railway antes de desplegar.

1. Entra en [Railway](https://railway.app/) y crea una cuenta usando **Continue with GitHub**.
2. Pulsa **New Project** > **Deploy from GitHub repo** y autoriza el acceso a `fruittales-video-pipeline`.
3. Selecciona el repositorio. En la configuración del servicio, establece **Root Directory** como `bot`.
4. Railway detectará Python. Si te pide comandos, usa:

   ```text
   Build: pip install -r requirements.txt
   Start: python main.py
   ```

5. Abre la pestaña **Variables** y crea, una a una, las mismas variables de `bot/.env`: `DISCORD_TOKEN`, `YOUTUBE_API_KEY`, `OWNER_USER_ID`, `DISCORD_CHANNEL_ID`, `YOUTUBE_CHANNEL_HANDLE`, `CHECK_INTERVAL_MINUTES` y, si la usas, las variables `NEXT_VIDEO_*`.
6. No subas ni copies el archivo `.env` al repositorio: Railway conserva esos valores como secretos del servicio.
7. Pulsa **Deploy**. En **Deployments > View Logs** deberías ver mensajes como `Comandos de aplicación sincronizados` y `Conectado como...`.
8. En Discord, prueba `/ping` y `/estado`. Si ambos responden, FruitTales Guardian funciona desde Railway y tu ordenador puede estar apagado.

Si Railway detiene el servicio por límites de plan, el bot se desconectará hasta que el servicio vuelva a estar activo. Render es una alternativa, pero sus Background Workers no tienen actualmente un plan gratuito.
