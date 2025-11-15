import discord
from discord import app_commands
from discord.ext import commands

from twilio.rest import Client

import os
import re
import json
import random
import asyncio
from dotenv import load_dotenv

import sqlite3

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

bot = commands.Bot(command_prefix=[], intents=intents)

ROLE_NAME = "surfer"
CHANNEL_ROLE_NAME = "gang"
CHANNEL_NAME = "silver-surfer"
ALLOWED_GUILD=1432159080067235944

# regex match for US/Canada phone numbers
phone_regex = re.compile(r"^\+1\d{10}$")

# --- LOCAL FILE STORAGE --- #

# PHONES_FILE = "phones.json"
# REACTION_FILE = "reaction_messages.json"

# if os.path.exists(PHONES_FILE):
#     with open(PHONES_FILE, "r") as f:
#         user_phones = json.load(f)

# if os.path.exists(REACTION_FILE):
#     with open(REACTION_FILE, "r") as f:
#         reaction_messages = json.load(f)

# def save_phone_data():
#     with open(PHONES_FILE, "w") as f:
#         json.dump(user_phones, f)

# def save_reaction_messages():
#     with open(REACTION_FILE, "w") as f:
#         json.dump(reaction_messages, f)

# --- SQLITE DATABASE --- #

db = sqlite3.connect("data.db")
db.row_factory = sqlite3.Row # so we can use rowss as dictionaries and not just tuples, e.g., row["phone"]
cur = db.cursor()

def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS phones (
        user_id TEXT PRIMARY KEY,
        phone TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reaction_messages (
        guild_id TEXT PRIMARY KEY,
        message_id TEXT
    )
    """)

    db.commit()

### PHONE NUMBERS

def get_phone(user_id: str):
    cur.execute("SELECT phone FROM phones WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return row["phone"] if row else None

def set_phone(user_id: str, phone: str):
    cur.execute("REPLACE INTO phones (user_id, phone) VALUES (?, ?)", (user_id, phone))
    db.commit()

def delete_phone(user_id: str):
    cur.execute("DELETE FROM phones WHERE user_id = ?", (user_id,))
    db.commit()

def delete_all_phones():
    cur.execute("DELETE FROM phones")
    db.commit()

### REACTION MESSAGES

def get_reaction_message(guild_id: str):
    cur.execute("SELECT message_id FROM reaction_messages WHERE guild_id = ?", (guild_id,))
    row = cur.fetchone()
    return row["message_id"] if row else None

def set_reaction_message(guild_id: str, message_id: str):
    cur.execute("REPLACE INTO reaction_messages (guild_id, message_id) VALUES (?, ?)",
                (guild_id, message_id))
    db.commit()

async def ensure_role_exists(guild: discord.Guild, role_name: str = ROLE_NAME):
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        return role
    
    print(f"create role {role_name}")
    role = await guild.create_role(name=role_name, color=discord.Color.blue(), mentionable=True)
    return role

async def ensure_channel_exists(guild: discord.Guild, channel_name: str = CHANNEL_NAME, role_name = CHANNEL_ROLE_NAME):
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        print("no role found")
        return None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        role: discord.PermissionOverwrite(view_channel=True)
    }

    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel is None:
        print(f"creating channel {channel_name}")
        channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )

        return channel
    return channel

@bot.event
async def on_ready():
    """runs when bot start up"""
    print(f'logged in as {bot.user}')

    for guild in bot.guilds:
        if guild.id != ALLOWED_GUILD:
            print(f"Leaving unauthorized guild: {guild.name} ({guild.id})")
            await guild.leave()
            continue

        await ensure_role_exists(guild)
        await ensure_channel_exists(guild)

    await bot.tree.sync()

@bot.event
async def on_guild_join(guild: discord.Guild):
    """runs when joins a new server"""
    await ensure_role_exists(guild)

@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    
    # msg_id = reaction_messages.get(str(guild.id))
    msg_id = get_reaction_message(str(guild.id))
    if msg_id is None or payload.message_id != int(msg_id) or payload.user_id == bot.user.id:
        return

    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None:
        print("role surfer not found")
        return

    if str(payload.emoji) == "🌊":
        member = guild.get_member(payload.user_id)
        if member:
            await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    
    # msg_id = reaction_messages.get(str(guild.id))
    msg_id = get_reaction_message(str(guild.id))
    if msg_id is None or payload.message_id != int(msg_id):
        return

    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None:
        return

    if str(payload.emoji) == "🌊":
        member = guild.get_member(payload.user_id)
        if member:
            await member.remove_roles(role)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.lower().strip() == "what":
        monkey_path = "gifs/monkey.png"
        file = discord.File(monkey_path, filename="monkey.png")
        await message.channel.send(file=file)


@bot.tree.command(name="surferrole", description="send the reaction-role message")
async def surferrole(interaction: discord.Interaction):
    if interaction.channel.name != CHANNEL_NAME:
        await interaction.response.send_message(f"please use this command in the `#{CHANNEL_NAME}` channel", ephemeral=True)
        return

    await interaction.response.send_message("posting surfer role message", ephemeral=True)

    await ensure_role_exists(interaction.guild)

    embed = discord.Embed(
        title="🏄 silva surfers",
        description="react with 🌊 to get the **surfer** role.",
        color=discord.Color.blue()
    )

    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🌊")

    # reaction_messages[str(interaction.guild.id)] = msg.id
    # save_reaction_messages()

    set_reaction_message(str(interaction.guild.id), str(msg.id))

@bot.tree.command(name="surf", description="ping all surfers")
async def surf(interaction: discord.Interaction):
    await interaction.response.send_message("pinging all surfers", ephemeral=True)
    
    guild = interaction.guild

    surfer_role = discord.utils.get(guild.roles, name=ROLE_NAME)

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
    await interaction.channel.send(content=surfer_role.mention, file=file)

async def get_phone_number(interaction: discord.Interaction, user: discord.User):
    """get phone number of a user"""
    uid = str(user.id)
    # phone_number = user_phones.get(uid)
    phone_number = get_phone(uid)

    if not phone_number:
        await interaction.channel.send(f"{user}'s phone number is not registered, check dms")
        await user.send(f"register {user}'s phone number here pls, type the 10 digits, no `+1`, no spaces, no dashes, no parentheses. type `cancel` to cancel")

        def check(m):
            return isinstance(m.channel, discord.DMChannel) and m.author.id == user.id

        try:
            reply = await bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            await user.send("phone number registration timed out")
            return None

        if reply.content.lower() == "cancel":
            await user.send("registration cancelled")
            return None

        phone_number = "+1" + reply.content.strip()
        if not phone_regex.match(phone_number):
            await user.send("⚠️ invalid format, registration cancelled")
            return None

        # user_phones[uid] = phone_number
        # save_phone_data()
        set_phone(uid, phone_number)
        await user.send(f"saved {user}'s number as {phone_number}.")

    return phone_number

@bot.tree.command(name="call", description="call a surfer")
@app_commands.describe(user="user to call", message="message to say in the call")
async def call(interaction: discord.Interaction, user: discord.User, message: str):
    await interaction.response.send_message(f"calling {user}")
    phone_number = await get_phone_number(interaction, user)
    if not phone_number:
        return

    try:
        twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_NUMBER,
            twiml=f"<Response><Pause length='2'/><Say>{message}</Say><Pause length='1'/></Response>"
        )
        await interaction.channel.send("called diddyblud")
    except Exception as e:
        await interaction.channel.send("call failed")
        print(f"twilio error: {e}")

@bot.tree.command(name="message", description="message a surfer")
@app_commands.describe(user="user to message", message="content of the message")
async def message(interaction: discord.Interaction, user: discord.User, message: str):
    await interaction.response.send_message(f"messaging {user}")
    phone_number = await get_phone_number(interaction, user)
    if not phone_number:
        return

    try:
        twilio_client.messages.create(
            to=phone_number,
            from_=TWILIO_NUMBER,
            body=message
        )
        await interaction.channel.send(f"messaged {user}")
    except Exception as e:
        await interaction.channel.send("message failed")
        print(f"twilio error: {e}")

@bot.tree.command(name="updatephonenumber", description="update a phone number")
@app_commands.describe(user="user whos phone number to update", phone_number="new phone number")
async def updatephonenumber(interaction: discord.Interaction, user: discord.User, phone_number: str):
    await interaction.response.send_message(f"updating {user}'s number", ephemeral=True)

    if not phone_number.startswith("+1"):
        phone_number = "+1" + phone_number.strip()
    
    if not phone_regex.match(phone_number):
        await interaction.channel.send("invalid phone number format")
        return

    uid = str(user.id)
    # user_phones[uid] = phone_number
    # save_phone_data()
    set_phone(uid, phone_number)
    await interaction.channel.send(f"updated {user}'s phone number to {phone_number}.")

@bot.tree.command(name="deletephonenumber", description="delete a phone number")
@app_commands.describe(user="user whose phone number to delete")
async def deletephonenumber(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message(f"deleting {user}'s number", ephemeral=True)

    uid = str(user.id)
    current_phone = get_phone(uid)
    if current_phone is not None:
        # del user_phones[uid]
        # save_phone_data()
        delete_phone(uid)
        await interaction.channel.send(f"deleted {user}'s phone number")
    else:
        await interaction.channel.send(f"{user} does not have a registered phone number.")

@bot.tree.command(name="deleteallphonenumbers", description="delete all phone numbers")
async def deleteallphonenumbers(interaction: discord.Interaction):
    await interaction.response.send_message("deleting all phone numbers", ephemeral=True)
    # user_phones.clear()
    # save_phone_data()
    delete_all_phones()
    await interaction.channel.send("deleted all phone numbers")

init_db()
bot.run(TOKEN)