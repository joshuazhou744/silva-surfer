import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
reaction_message_id = None

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

@bot.command()
async def surferrole(ctx, channel_name: str = "general"):
    """Send the reaction-role message in a given channel"""
    channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
    if channel is None:
        await ctx.send(f"Couldn't find a #{channel_name} channel.")
        return

    embed = discord.Embed(
        title="🏄 silva surfers",
        description="react with 🌊 to get the **surfer** role.",
        color=discord.Color.blue()
    )

    msg = await channel.send(embed=embed)
    await msg.add_reaction("🌊")

    global reaction_message_id
    reaction_message_id = msg.id

@bot.event
async def on_raw_reaction_add(payload, role_name="surfer"):
    if payload.message_id != reaction_message_id or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        print("role surfer not found")
        return

    if str(payload.emoji) == "🌊":
        member = guild.get_member(payload.user_id)
        if member:
            await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload, role_name="surfer"):
    if payload.message_id != reaction_message_id:
        return

    guild = bot.get_guild(payload.guild_id)
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        return

    if str(payload.emoji) == "🌊":
        member = guild.get_member(payload.user_id)
        if member:
            await member.remove_roles(role)

@bot.command()
async def surf(ctx, role_name="surfer"):
    guild = bot.get_guild(ctx.guild.id)
    surfer_role = discord.utils.get(guild.roles, name=role_name)

    # gifs = [
    #     "https://tenor.com/view/silver-gif-10327880808519491874",
    #     "https://tenor.com/view/silver-surfer-gif-22251164",
    #     "https://tenor.com/view/marlon-streamer-marlon-streamer-lacy-mogged-gif-1741399791848271101",
    #     "https://tenor.com/view/silver-surfer-marvel-future-fight-marvel-future-revolution-netmarble-king-tron-gif-26435424",
    #     "https://tenor.com/view/silver-surfer-surfing-fantastic-four-gif-16035455",
    #     "https://tenor.com/view/silver-gif-10327880808519491874",
    #     "https://tenor.com/view/silver-surfer-gif-22251164",
    #     "https://tenor.com/view/marlon-streamer-marlon-streamer-lacy-mogged-gif-1741399791848271101",
    # ]
    # gif_url = random.choice(gifs)

    gif_files = [
        "gifs/1.gif",
        "gifs/2.gif",
        "gifs/3.gif",
        "gifs/4.gif",
        "gifs/5.gif",
        "gifs/6.gif",
        "gifs/7.gif",
        "gifs/8.gif",
    ]

    gif_path = random.choice(gif_files)

    file = discord.File(gif_path, filename="surf.gif")
    await ctx.send(content=surfer_role.mention, file=file)


@bot.command()
async def print_hist(ctx):
    messages = [m async for m in ctx.channel.history(limit=10, before=ctx.message)]

    transcript = "\n".join([f"{msg.author}: {msg.content}" for msg in reversed(messages)])
    await ctx.send(transcript)

bot.run(TOKEN)