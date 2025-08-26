# Discord Bot Setup Instructions

## Prerequisites
1. Python 3.8 or higher
2. Discord Developer Account

## Setup Steps

### 1. Create Discord Application
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Give it a name and create
4. Go to "Bot" section
5. Click "Add Bot"
6. Copy the bot token

### 2. Configure the Bot
1. Open `config.py`
2. Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token
3. Replace `YOUR_BOT_ID` in BOT_INVITE with your bot's client ID (from General Information)
4. Replace the DEVS tuple with your Discord user ID
5. Replace SERVER_ID with your Discord server ID
6. Update other URLs and IDs as needed

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# Initialize aerich (database migrations)
aerich init-db

# If you need to make changes later, use:
# aerich migrate
# aerich upgrade
```

### 5. Run the Bot
```bash
python bot.py
```

## Key Changes Made

### Database
- Converted from PostgreSQL to SQLite
- Database file will be created as `db.sqlite3`
- No need for external database setup

### Premium Features
- All premium restrictions removed
- Unlimited scrims, tournaments, and other features
- Everyone gets "premium" status by default
- All premium-only features are now free

### Features Now Available to Everyone
- Unlimited scrims (was limited to 3)
- Unlimited tournaments (was limited to 1) 
- Unlimited TagCheck channels (was limited to 1)
- Unlimited EasyTag channels (was limited to 1)
- Unlimited SSVerify channels (was premium only)
- Unlimited AutoPurge channels (was limited to 1)
- Custom reactions and emojis
- All screenshot verification types
- Success messages
- And much more!

## Getting Your Discord User ID
1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click your username and select "Copy ID"
3. Replace the ID in the DEVS tuple in config.py

## Getting Your Server ID
1. Right-click your server name and select "Copy ID"
2. Replace SERVER_ID in config.py

## Bot Permissions
When inviting the bot, make sure it has these permissions:
- Administrator (recommended for full functionality)
- Or at minimum: Manage Channels, Manage Roles, Manage Messages, Send Messages, Embed Links, Add Reactions, Use External Emojis

## Troubleshooting
- If you get import errors, make sure all dependencies are installed
- If database errors occur, delete `db.sqlite3` and run `aerich init-db` again
- Check that your bot token is correct and the bot is in your server
- Ensure the bot has proper permissions in your Discord server