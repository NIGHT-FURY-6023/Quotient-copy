# for tortoise-orm
TORTOISE = {
    "connections": {
        "default": "sqlite://db.sqlite3"
    },
    "apps": {
        "models": {
            "models": [
                "models.esports.scrims",
                "models.esports.slotm", 
                "models.esports.ssverify",
                "models.esports.tagcheck",
                "models.esports.tourney",
                "models.misc.guild",
                "models.misc.User",
                "models.misc.Votes",
                "models.misc.Commands",
                "models.misc.Tag",
                "models.misc.Timer",
                "models.misc.Snipe",
                "models.misc.AutoPurge",
                "models.misc.Autorole",
                "models.misc.Lockdown",
                "models.misc.alerts",
                "models.misc.block",
                "models.misc.premium",
                "aerich.models"
            ],
            "default_connection": "default",
        },
    },
}

POSTGRESQL = {}

EXTENSIONS = (
    "cogs.esports",
    "cogs.events", 
    "cogs.mod",
    "cogs.premium",
    "cogs.quomisc",
    "cogs.reminder",
    "cogs.utility",
    "jishaku",
)

# Bot Configuration
DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"

COLOR = 0x00FFB3
FOOTER = "quo is lub!"
PREFIX = "q"

# Links
SERVER_LINK = "https://discord.gg/your-server"
BOT_INVITE = "https://discord.com/oauth2/authorize?client_id=YOUR_BOT_ID&scope=bot&permissions=8"
WEBSITE = "https://your-website.com"
REPOSITORY = "https://github.com/your-repo"

# Developer IDs (replace with your Discord user ID)
DEVS = (123456789012345678,)  # Replace with your actual Discord user ID

# Server Configuration
SERVER_ID = 123456789012345678  # Replace with your server ID
SERVER_PORT = 8000

# Role IDs (replace with actual role IDs from your server)
VOTER_ROLE = 123456789012345678
PREMIUM_ROLE = 123456789012345678

# Webhook URLs (optional - can be left empty)
SHARD_LOG = ""
ERROR_LOG = ""
PUBLIC_LOG = ""

# Premium/Payment related (can be left empty since we're removing premium)
PAYU_KEY = ""
PAYU_SALT = ""
PAYU_PAYMENT_LINK = ""
SUCCESS_URL = ""
FAILED_URL = ""
PAY_LINK = ""
PRIME_EMOJI = "⭐"
PREMIUM_AVATAR = ""

# Socket/API related (optional)
SOCKET_URL = ""
SOCKET_AUTH = ""
FASTAPI_URL = ""
FASTAPI_KEY = ""

# Pro bot link (optional)
PRO_LINK = ""