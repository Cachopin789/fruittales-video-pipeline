# Changelog

Todos los cambios relevantes de FruitTales se documentan en este archivo.

## [2026-09-09] - Estructura visual del servidor Discord

### Mejorado

- `/configurar-servidor` crea canales y sala de voz con emojis para una estructura visual consistente.
- Los canales antiguos sin emoji se renombran y reubican automáticamente, sin crear duplicados.
- El resumen de configuración diferencia elementos creados, migrados y ya existentes.

## [2026-09-09] - Correcciones de fiabilidad del bot

### Corregido

- `/configurar-servidor` guarda automáticamente `#nuevos-videos` como destino de los avisos, con `DISCORD_CHANNEL_ID` como respaldo.
- El bot ya no solicita Message Content Intent, que no necesita al funcionar exclusivamente con comandos `/`.
- Protección global contra menciones accidentales en los mensajes enviados por el bot.

## [2026-09-09] - Arranque local robusto del bot

### Corregido

- La carga de `bot/.env` ya no depende de la carpeta desde la que se ejecute Python; el bot puede iniciarse correctamente desde la raíz del repositorio.

## [2026-09-09] - Configuración inicial del servidor Discord

### Añadido

- Comando exclusivo `/configurar-servidor`, protegido por `OWNER_USER_ID`, para crear la estructura profesional del servidor sin duplicar roles ni canales.
- Creación idempotente de categorías, canales, sala de voz y roles `Admin` y `Miembro`, con permisos de solo lectura en `#anuncios` para la comunidad.
- Asignación automática del rol `Miembro` a nuevas entradas cuando Server Members Intent está habilitado.
- Documentación del comando, permisos necesarios y configuración segura del propietario.

## [2026-09-09] - Aclaración de documentación del proyecto

### Corregido

- README principal actualizado para diferenciar el pipeline de vídeo, que no requiere Python ni credenciales, del componente independiente FruitTales Guardian.
- Estructura, características y configuración documentadas con las funciones reales del bot y la ubicación segura de sus secretos.

## [2026-09-08] - Ampliación de FruitTales Guardian

### Añadido

- Comandos `/ayuda`, `/canal`, `/random`, `/proximo` y `/estado`.
- Configuración opcional de la próxima publicación mediante `NEXT_VIDEO_AT`, `NEXT_VIDEO_TITLE` y `NEXT_VIDEO_URL`.
- Documentación Markdown individual para todos los comandos dentro de `bot/comandos-docs/`.
- Guía paso a paso para desplegar FruitTales Guardian en Railway y comprobar su funcionamiento.
- Calendario versionado `bot/programacion.json` para que `/proximo` avance automáticamente a la siguiente publicación programada.

### Mejorado

- Identidad visual y mensajes del bot con la marca FruitTales Guardian, embeds y mensajes de error más cercanos.
- Cliente de YouTube con consulta de información general del canal y recomendación aleatoria limitada a los 50 vídeos más recientes para controlar la cuota.

## [2026-09-08] - Bot de Discord para FruitTalesES

### Añadido

- Bot independiente en `bot/`, implementado con Python y `discord.py`.
- Avisos automáticos de nuevos vídeos del canal `FruitTalesES`, con título, enlace y miniatura.
- Comandos `/stats`, `/ultimovideo`, `/ping` y `/uptime`.
- Integración segura con YouTube Data API v3 mediante variables de entorno.
- README específico del bot, archivo de dependencias, plantilla `.env.example` y guía de despliegue.
- Exclusión de secretos, cachés y entornos virtuales mediante `.gitignore`.

### Mejorado

- Horario de avisos en hora de España (`Europe/Madrid`): solo se consulta YouTube entre las 15:00 y las 21:00, con un intervalo mínimo de 30 minutos.
- Embeds profesionales para los avisos, el último vídeo y las estadísticas del canal.
- Reintentos ante fallos temporales de YouTube y Discord, protección frente a avisos duplicados y persistencia segura del estado.
- Logging de actividad en consola y en archivos rotativos dentro de `bot/logs/`.

> Esta entrada resume la primera integración del bot. Los commits anteriores a esta fecha no incluían código de Discord.
