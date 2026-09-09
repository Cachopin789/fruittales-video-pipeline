"""Utilidades de comunidad para sugerencias, encuestas y normas."""
import discord

BRAND_RED = 0xE74C3C
NUMBER_EMOJIS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣")

def find_text_channel(guild: discord.Guild, *names: str) -> discord.TextChannel | None:
    """Busca el primer canal de texto cuyo nombre coincida con las alternativas."""
    for name in names:
        channel = discord.utils.get(guild.text_channels, name=name)
        if channel:
            return channel
    return None

def suggestion_embed(author: discord.abc.User, idea: str) -> discord.Embed:
    embed = discord.Embed(title="💡 Nueva sugerencia de la comunidad", description=idea, color=BRAND_RED)
    embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
    embed.set_footer(text=f"Usuario ID: {author.id} · FruitTales Guardian")
    return embed

def poll_embed(question: str, options: list[str], author: discord.abc.User) -> discord.Embed:
    lines = [f"{NUMBER_EMOJIS[index]} **{option}**" for index, option in enumerate(options)]
    embed = discord.Embed(title="📊 Encuesta de FruitTales", description=f"**{question}**\n\n" + "\n".join(lines), color=BRAND_RED)
    embed.set_footer(text=f"Creada por {author.display_name} · Vota con una reacción")
    return embed
