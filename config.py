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
DISCORD_TOKEN = ""

COLOR = 0x00FFB3
FOOTER = "under devlopement!"
PREFIX = "q"

# Links
SERVER_LINK = "https://discord.gg/HuXybWkK"
BOT_INVITE = "https://discord.com/oauth2/authorize?client_id=YOUR_BOT_ID&scope=bot&permissions=8"
WEBSITE = "https://your-website.com"
REPOSITORY = "https://github.com/your-repo"

# Developer IDs (replace with your Discord user ID)
DEVS = (761635564835045387,)  # Replace with your actual Discord user ID

# Server Configuration
SERVER_ID = 1242541956161081414  # Replace with your server ID
SERVER_PORT = 8000

# Role IDs (replace with actual role IDs from your server)
VOTER_ROLE = 1410147134233247794
PREMIUM_ROLE = 1410147134233247794

# Webhook URLs (optional - can be left empty)
SHARD_LOG = "https://discord.com/api/webhooks/1410048134863650920/xxzptnWTcxisa0rnAKfTtUSos2aicU9KiSYIk3kIIg_16M8K8sC5oBvyJjf8CNabo-VJ"
ERROR_LOG = "https://discord.com/api/webhooks/1410048134863650920/xxzptnWTcxisa0rnAKfTtUSos2aicU9KiSYIk3kIIg_16M8K8sC5oBvyJjf8CNabo-VJ"
PUBLIC_LOG = "https://discord.com/api/webhooks/1410048134863650920/xxzptnWTcxisa0rnAKfTtUSos2aicU9KiSYIk3kIIg_16M8K8sC5oBvyJjf8CNabo-VJ"

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