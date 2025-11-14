import discord
from discord.ext import commands

from twilio.rest import Client

import os
import re
import json
from dotenv import load_dotenv
import random

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = Client(account_sid, auth_token)
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")


TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True


bot = commands.Bot(command_prefix='!', intents=intents)

reaction_message_id = None
DATA_FILE = "phones.json"
user_phones = {}

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_phones = json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_phones, f)

# regrex match for US/Canada phone numbers
phone_regex = re.compile(r"^\+1\d{10}$")

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

@bot.command()
async def surferrole(ctx):
    """send the reaction-role message"""

    embed = discord.Embed(
        title="🏄 silva surfers",
        description="react with 🌊 to get the **surfer** role.",
        color=discord.Color.blue()
    )

    msg = await ctx.send(embed=embed)
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
    """ping all surfers"""
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

async def get_phone_number(ctx, user: discord.User):
    """get phone number of a user"""
    uid = str(user.id)
    phone_number = user_phones.get(uid)

    if not phone_number:
        await ctx.send(f"{user}'s phone number is not registered, check dms")
        await user.send(f"register {user}'s phone number here pls, type the 10 digits, no `+1`, no spaces, no dashes, no parentheses. type `cancel` to cancel")

        def check(m):
            return isinstance(m.channel, discord.DMChannel)

        try:
            reply = await bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            await user.send("phone number registration timed out")
            return None

        if reply.content.lower() == "cancel":
            await user.send("registration cancelled")
            return None

        phone_number = "+1" + reply.content.strip()
        if not phone_regex.match(phone_number):
            await user.send("⚠️ invalid format, registration cancelled")
            return None

        user_phones[uid] = phone_number
        save_data()
        await user.send(f"saved number as {phone_number}.")

    return phone_number

@bot.command()
async def call(ctx, user: discord.User, message: str, twilio_number = TWILIO_NUMBER):
    """call a surfer, usage: !call @user 'your message here'"""
    phone_number = await get_phone_number(ctx, user)
    if not phone_number:
        return

    try:
        twilio_client.calls.create(
            to=phone_number,
            from_=twilio_number,
            twiml=f"<Response><Pause length='3'/><Say>{message}</Say></Response>"
        )
        await ctx.send(f"calling diddyblud")
    except Exception as e:
        await ctx.send("failed calling")
        await print(f"twilio error: {e}")

@bot.command()
async def message(ctx, user: discord.User, message: str, twilio_number = TWILIO_NUMBER):
    """message a surfer, usage: !message @user 'your message here'"""
    command = bot.get_command("call")
    temp = f"!{command.name} {command.signature}"
    print(temp)
    phone_number = await get_phone_number(ctx, user)
    if not phone_number:
        return

    try:
        twilio_client.messages.create(
            to=phone_number,
            from_=twilio_number,
            body=message
        )
        await ctx.send(f"messaged {user}")
    except Exception as e:
        await ctx.send("failed messaging")
        print(f"twilio error: {e}")


bot.run(TOKEN)