# /configurar-servidor

**Qué hace:** crea la estructura inicial de FruitTales: categorías, canales con emojis, roles `Admin`, `Miembro` y `Bots`, la sala de voz `🔊 Sala general` y el canal privado `🤖│bot-comandos` dentro de `🤖 BOTS`.

**Uso:** `/configurar-servidor`

**Ejemplo:** un embed privado con los elementos creados, migrados desde nombres antiguos, los ya existentes y `🔔│nuevos-videos` ya vinculado a los avisos automáticos.

**Privacidad:** `💬│general` y `🔔│nuevos-videos` son públicos. El resto de canales, incluida la voz, queda oculto para `@everyone` y visible para el propietario y los bots. Discord no ofrece un permiso global para bots futuros: asígnales el rol `Bots` (o Administrador) para que puedan usar los canales privados.

**Limitaciones:** solo funciona para el usuario indicado en `OWNER_USER_ID`, dentro de un servidor, y con el bot teniendo permiso de Administrador. Es seguro repetirlo: no duplica nombres existentes, reanuda una configuración interrumpida, renombra los nombres antiguos sin emoji y reaplica los permisos. Para asignar automáticamente el rol `Miembro` a nuevas entradas, activa **Server Members Intent** en Discord Developer Portal.
