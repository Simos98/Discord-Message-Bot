# Discord-Message-Bot
A subscription based messaging bot for Discord to manage and assist large group coordination.

## Setup

1. Clone this repo and enter the folder.
2. Create a virtual environment:
```
   python -m venv venv
```
3. Activate it:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies:
```
   pip install -r requirements.txt
```
5. Create a `.env` file in the project folder with:
```
   DISCORD_TOKEN=your_bot_token_here
   ADMIN_USER_ID=your_discord_user_id_here
```
6. Run the bot:
```
   python bot.py
```

## Commands

- `/subscribe` — Join the broadcast list
- `/unsubscribe` — Leave the broadcast list
- `/broadcast message:<text>` — (Admin only) Send a DM to all subscribers
