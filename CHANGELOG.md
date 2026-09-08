# Changelog

Todos los cambios relevantes de FruitTales se documentan en este archivo.

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
