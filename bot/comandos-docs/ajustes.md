# /ajustes

**Qué hace:** consulta o modifica la configuración persistente de FruitTales Guardian. Los valores se guardan en `bot/config_bot.json`, separado del pipeline de vídeo y sin secretos.

**Uso:**

- `/ajustes ver`
- `/ajustes cambiar-horario inicio:<HH:MM> fin:<HH:MM>`
- `/ajustes cambiar-canal-avisos canal:<canal de texto>`

**Ejemplo:** `/ajustes cambiar-horario inicio:16:00 fin:20:30` cambia la franja de consultas a 16:00–20:30 en hora de España.

**Limitaciones:** solo puede usarlo `OWNER_USER_ID`. El inicio debe ser anterior al fin durante el mismo día. El intervalo mínimo sigue siendo 30 minutos para proteger la cuota de YouTube. `/ajustes ver` nunca muestra el token de Discord ni la clave de YouTube.
