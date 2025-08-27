from __future__ import annotations

import discord
from core import Quotient
from .commands import Premium
from .expire import deactivate_premium, extra_guild_perks, remind_guild_to_pay, remind_user_to_pay
from models import PremiumPlan
from .views import PremiumView

__all__ = ("setup",)

async def setup(bot: Quotient):
    # Insert default plans if none exist
    await PremiumPlan.insert_plans()
    
    # Add persistent view
    bot.add_view(PremiumView(bot))
    
    # Add the Premium cog
    await bot.add_cog(Premium(bot))
