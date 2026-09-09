# /configurar-servidor

**Qué hace:** crea la estructura inicial de FruitTales: categorías, canales con emojis, roles `Admin` y `Miembro`, y la sala de voz `🔊 Sala general`. En `📌│anuncios` solo el bot y el rol Admin pueden escribir.

**Uso:** `/configurar-servidor`

**Ejemplo:** un embed privado con los elementos creados, migrados desde nombres antiguos, los ya existentes y `🔔│nuevos-videos` ya vinculado a los avisos automáticos.

**Limitaciones:** solo funciona para el usuario indicado en `OWNER_USER_ID`, dentro de un servidor, y con el bot teniendo permiso de Administrador. Es seguro repetirlo: no duplica nombres existentes y renombra los nombres antiguos sin emoji. Para asignar automáticamente el rol `Miembro` a nuevas entradas, activa **Server Members Intent** en Discord Developer Portal.
