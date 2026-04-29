import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
SUBSCRIBER_FILE = DATA_DIR / "subscribers.json"
SUB_ADMIN_FILE = DATA_DIR / "sub_admins.json"

BROADCAST_DELAY_SECONDS = 1.0 # Delay between sending messages to avoid rate limitting

load_dotenv(dotenv_path=ENV_PATH)
TOKEN = os.getenv('DISCORD_TOKEN')
#ADMIN_IDS = {int(os.getenv('ADMIN_USER_ID'))} # Load admin user IDs from .env

main_admin_id_str = os.getenv("ADMIN_USER_ID")
if not main_admin_id_str:
    raise RuntimeError("ADMIN_USER_ID is missing in .env")

try:
    MAIN_ADMIN_ID = int(main_admin_id_str)
except ValueError:
    raise RuntimeError("ADMIN_USER_ID must be an integer Discord user ID")

ADMIN_IDS = {MAIN_ADMIN_ID}

# Both functions assist in remembering who is subscribed to the broadcast messages across bot restarts.
def load_subscribers(): #Function to load subscribers from a JSON file, returns a set of subscriber IDs
    if SUBSCRIBER_FILE.exists():
        return set(json.loads(SUBSCRIBER_FILE.read_text(encoding="utf-8")))
    return set()

def save_subscribers(subscribers): # Function to save subscribers to a JSON file, takes a set of subscriber IDs and writes it to the file
    SUBSCRIBER_FILE.write_text(json.dumps(list(subscribers)), encoding="utf-8")

def load_sub_admins():
    if SUB_ADMIN_FILE.exists():
        return set(json.loads(SUB_ADMIN_FILE.read_text(encoding="utf-8")))
    return set()

def save_sub_admins(sub_admins):
    SUB_ADMIN_FILE.write_text(json.dumps(list(sub_admins)), encoding="utf-8")

def is_main_admin(user_id: int) -> bool:
    return user_id == MAIN_ADMIN_ID

def can_broadcast(user_id: int, sub_admins: set[int]) -> bool:
    return is_main_admin(user_id) or user_id in sub_admins

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

subscribers = load_subscribers() # Load subscribers when the bot starts
sub_admins = load_sub_admins() # Load sub-admins when the bot starts

@bot.event
async def on_ready():
    await bot.tree.sync() # Syncs the command tree with Discord, ensuring that all registered commands are available
    print(f'Logged in as {bot.user}')

@bot.tree.command(description="Subscribe to broadcast messages")
async def subscribe(interaction: discord.Interaction):
    subscribers.add(interaction.user.id) # Adds the user's ID to the set of subscribers
    save_subscribers(subscribers) # Saves the updated set of subscribers to the JSON file
    await interaction.response.send_message("You have subscribed to broadcast messages!", ephemeral=True)

@bot.tree.command(description="Unsubscribe from broadcasts")
async def unsubscribe(interaction: discord.Interaction):
    subscribers.discard(interaction.user.id) # Removes the user's ID from the set of subscribers
    save_subscribers(subscribers) # Saves the updated set of subscribers to the JSON file
    await interaction.response.send_message("You're now unsubscribed from broadcast messages.", ephemeral=True)

@bot.tree.command(description="Broadcast a message to all subscribers (admin only)")
async def broadcast(interaction: discord.Interaction, message: str):
    if not can_broadcast(interaction.user.id, sub_admins):
        await interaction.response.send_message("Not authorized.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    sent, failed = 0, 0
    for user_id in subscribers:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(message)
            sent += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY_SECONDS) # Delay to avoid hitting rate limits
    await interaction.followup.send(f"Sent to {sent}, failed {failed}.", ephemeral=True)

@bot.tree.command(description="Main admin: set delay (seconds) between broadcast DMs")
async def broadcast_delay(interaction: discord.Interaction, seconds: float):
    global BROADCAST_DELAY_SECONDS

    if not is_main_admin(interaction.user.id):
        await interaction.response.send_message("Only the main admin can do this.", ephemeral=True)
        return

    if seconds < 0 or seconds > 60:
        await interaction.response.send_message(
            "Delay must be between 0 and 60 seconds.", ephemeral=True
        )
        return

    BROADCAST_DELAY_SECONDS = seconds
    await interaction.response.send_message(
        f"Broadcast delay set to {seconds:.2f} seconds.", ephemeral=True
    )

@bot.tree.command(description="Main admin: add a sub-admin")
async def add_sub_admin(interaction: discord.Interaction, user: discord.User):
    if not is_main_admin(interaction.user.id):
        await interaction.response.send_message("Only the main admin can do this.", ephemeral=True)
        return

    if user.id == MAIN_ADMIN_ID:
        await interaction.response.send_message("Main admin is already allowed.", ephemeral=True)
        return

    sub_admins.add(user.id)
    save_sub_admins(sub_admins)
    await interaction.response.send_message(f"Added {user.mention} as sub-admin.", ephemeral=True)

@bot.tree.command(description="Main admin: remove a sub-admin")
async def remove_sub_admin(interaction: discord.Interaction, user: discord.User):
    if not is_main_admin(interaction.user.id):
        await interaction.response.send_message("Only the main admin can do this.", ephemeral=True)
        return

    if user.id in sub_admins:
        sub_admins.remove(user.id)
        save_sub_admins(sub_admins)
        await interaction.response.send_message(f"Removed {user.mention} from sub-admins.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{user.mention} is not a sub-admin.", ephemeral=True)

@bot.tree.command(description="Main admin: list sub-admins")
async def list_sub_admins(interaction: discord.Interaction):
    if not is_main_admin(interaction.user.id):
        await interaction.response.send_message("Only the main admin can do this.", ephemeral=True)
        return

    if not sub_admins:
        await interaction.response.send_message("No sub-admins set.", ephemeral=True)
        return

    mentions = ", ".join(f"<@{uid}>" for uid in sorted(sub_admins))
    await interaction.response.send_message(f"Sub-admins: {mentions}", ephemeral=True)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file.")
    bot.run(TOKEN)