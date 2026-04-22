import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_IDS = {int(os.getenv('ADMIN_USER_ID')): 'AdminName'} # Load admin user IDs from .env
SUBSCRIBER_FILE = Path('subscribers.json')

# Both functions assist in remembering who is subscribed to the broadcast messages across bot restarts.
def load_subscribers(): #Function to load subscribers from a JSON file, returns a set of subscriber IDs
    if SUBSCRIBER_FILE.exists():
        return set(json.loads(SUBSCRIBER_FILE.read_text()))
    return set()

def save_subscribers(subscribers): # Function to save subscribers to a JSON file, takes a set of subscriber IDs and writes it to the file
    SUBSCRIBER_FILE.write_text(json.dumps(list(subscribers)))

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
subscribers = load_subscribers() # Load subscribers when the bot starts

@bot.event # What does the @ symbol do in Python?
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
    subscribers.discard(interaction.user.id)
    save_subscribers(subscribers)
    await interaction.response.send_message("You're now unsubscribed from broadcast messages.", ephemeral=True)

@bot.tree.command(description="Broadcast a message to all subscribers (admin only)")
async def broadcast(interaction: discord.Interaction, message: str):
    if interaction.user.id not in ADMIN_IDS:
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
    await interaction.followup.send(f"Sent to {sent}, failed {failed}.", ephemeral=True)