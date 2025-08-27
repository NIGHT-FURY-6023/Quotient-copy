from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from discord.ext import tasks

import config
from core import Cog


class QuoTasks(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.insert_guilds.start()

    @tasks.loop(count=1)
    async def insert_guilds(self):
        for guild in self.bot.guilds:
            query = """
            INSERT INTO guild_data (
                guild_id, prefix, embed_color, embed_footer, tag_enabled_for_everyone, 
                is_premium, premium_notified, public_profile, dashboard_access
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO NOTHING;
            """
            params = [
                guild.id, config.PREFIX, config.COLOR, config.FOOTER,
                True,  # tag_enabled_for_everyone
                True,  # is_premium
                False,  # premium_notified
                True,  # public_profile
                '{"embed": [], "scrims": [], "tourney": [], "slotm": []}'  # dashboard_access
            ]
            try:
                await self.bot.db.execute_query(query, params)
            except Exception as e:
                print(f"Error inserting guild {guild.id}: {e}")

    @insert_guilds.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()
