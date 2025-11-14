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


bot = commands.Bot(command_prefix="!", intents=intents)

reaction_message_id = None
ROLE_NAME = "surfer"
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

async def ensure_role_exists(guild: discord.Guild, role_name: str = ROLE_NAME):
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        return role
    
    print(f"create role {role_name}")
    role = await guild.create_role(name=role_name, color=discord.Color.blue(), mentionable=True)
    return role

@bot.event
async def on_ready():
    """runs when bot start up"""
    print(f'logged in as {bot.user}')

    for guild in bot.guilds:
        await ensure_role_exists(guild)

    await bot.tree.sync()

@bot.event
async def on_guild_join(guild: discord.Guild):
    """runs when joins a new server"""
    await ensure_role_exists(guild)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != reaction_message_id or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
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
    if payload.message_id != reaction_message_id:
        return

    guild = bot.get_guild(payload.guild_id)
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None:
        return

    if str(payload.emoji) == "🌊":
        member = guild.get_member(payload.user_id)
        if member:
            await member.remove_roles(role)


@bot.tree.command(name="surferrole", description="send the reaction-role message")
async def surferrole(interaction: discord.Interaction):
    await interaction.response.send_message("posting surfer role message", ephemeral=True)

    await ensure_role_exists(interaction.guild)

    embed = discord.Embed(
        title="🏄 silva surfers",
        description="react with 🌊 to get the **surfer** role.",
        color=discord.Color.blue()
    )

    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("🌊")

    global reaction_message_id
    reaction_message_id = msg.id

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
    phone_number = user_phones.get(uid)

    if not phone_number:
        await interaction.channel.send(f"{user}'s phone number is not registered, check dms")
        await user.send(f"register {user}'s phone number here pls, type the 10 digits, no `+1`, no spaces, no dashes, no parentheses. type `cancel` to cancel")

        def check(m):
            return isinstance(m.channel, discord.DMChannel) and m.author.id == interaction.user.id

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

        user_phones[uid] = phone_number
        save_data()
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

@bot.tree.command(name="updatephonenumber", description="update a user's phone number")
@app_commands.describe(user="user whos phone number to update", phone_number="new phone number")
async def updatephonenumber(interaction: discord.Interaction, user: discord.User, phone_number: str):
    await interaction.response.send_message(f"updating {user}'s number", ephemeral=True)

    if not phone_number.startswith("+1"):
        phone_number = "+1" + phone_number.strip()
    
    if not phone_regex.match(phone_number):
        await interaction.channel.send("invalid phone number format")
        return

    uid = str(user.id)
    if uid in user_phones:
        user_phones[uid] = phone_number
        save_data()
        await interaction.channel.send(f"updated {user}'s phone number to {phone_number}.")
    else:
        await interaction.channel.send(f"{user} does not have a registered phone number.")

@bot.tree.command(name="deletephonenumber", description="delete a user's phone number")
@app_commands.describe(user="user whose phone number to delete")
async def deletephonenumber(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message(f"deleting {user}'s number", ephemeral=True)

    uid = str(user.id)
    if uid in user_phones:
        del user_phones[uid]
        save_data()
        await interaction.channel.send(f"deleted {user}'s phone number")
    else:
        await interaction.channel.send(f"{user} does not have a registered phone number.")

@bot.tree.command(name="deleteallphonenumbers", description="delete all phone numbers")
async def deleteallphonenumbers(interaction: discord.Interaction):
    await interaction.response.send_message("deleting all phone numbers", ephemeral=True)
    user_phones.clear()
    save_data()
    await interaction.channel.send("deleted all phone numbers")


bot.run(TOKEN)