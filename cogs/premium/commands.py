from __future__ import annotations

import typing
from datetime import datetime, timedelta

import discord
from core import Cog, Context, Quotient
from discord.ext import commands
from models import Guild, PremiumTxn, User
from utils import emote


class Premium(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def premium(self, ctx: Context):
        """View premium status of yourself and the server"""
        
        user = await User.get(pk=ctx.author.id)
        guild = await Guild.get(guild_id=ctx.guild.id)
        
        user_premium = "Yes! (Free for everyone)" if not user.premium_expire_time else "Yes!"
        user_end = "Never" if not user.premium_expire_time else discord.utils.format_dt(user.premium_expire_time)
        
        guild_premium = "Yes! (Free for everyone)" if not guild.premium_end_time else "Yes!"
        guild_end = "Never" if not guild.premium_end_time else discord.utils.format_dt(guild.premium_end_time)
        guild_upgrader = "Unknown" if not guild.made_premium_by else f"<@{guild.made_premium_by}>"
        
        embed = discord.Embed(
            title="Quotient Premium",
            color=self.bot.color,
        )
        embed.add_field(
            name="User",
            value=(
                f"**Activated:** {user_premium}\n"
                f"**Ending:** {user_end}"
            ),
            inline=False
        )
        embed.add_field(
            name="Server", 
            value=(
                f"**Activated:** {guild_premium}\n"
                f"**Ending:** {guild_end}\n"
                f"**Originally Upgraded by:** {guild_upgrader}"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @premium.command(name="grant")
    @commands.is_owner()
    async def premium_grant(
        self,
        ctx: Context,
        target: typing.Union[discord.Member, discord.Guild],
        duration: int = 30,
    ):
        """Grant premium to a user or server (owner only)"""
        
        end_time = discord.utils.utcnow() + timedelta(days=duration)
        
        if isinstance(target, discord.Member):
            # Grant user premium
            await User.filter(pk=target.id).update(
                premium_expire_time=end_time,
                is_premium=True
            )
            
            # Try to give premium role
            if self.bot.config.PREMIUM_ROLE:
                try:
                    await target.add_roles(
                        discord.Object(id=self.bot.config.PREMIUM_ROLE),
                        reason="Premium granted"
                    )
                except discord.HTTPException:
                    pass
            
            await ctx.success(f"Granted premium to {target.mention} for {duration} days!")
            
        else:
            # Grant server premium
            await Guild.filter(guild_id=target.id).update(
                premium_end_time=end_time,
                is_premium=True,
                made_premium_by=ctx.author.id,
            )
            
            await ctx.success(f"Granted premium to server {target.name} for {duration} days!")

    @premium.command(name="revoke")
    @commands.is_owner() 
    async def premium_revoke(
        self,
        ctx: Context,
        target: typing.Union[discord.Member, discord.Guild],
    ):
        """Revoke premium from a user or server (owner only)"""
        
        if isinstance(target, discord.Member):
            # Revoke user premium
            await User.filter(pk=target.id).update(
                premium_expire_time=None,
                is_premium=False
            )
            
            # Try to remove premium role
            if self.bot.config.PREMIUM_ROLE:
                try:
                    await target.remove_roles(
                        discord.Object(id=self.bot.config.PREMIUM_ROLE),
                        reason="Premium revoked"
                    )
                except discord.HTTPException:
                    pass
                    
            await ctx.success(f"Revoked premium from {target.mention}!")
            
        else:
            # Revoke server premium
            await Guild.filter(guild_id=target.id).update(
                premium_end_time=None,
                is_premium=False,
                made_premium_by=None
            )
            
            await ctx.success(f"Revoked premium from server {target.name}!")


async def setup(bot: Quotient):
    await bot.add_cog(Premium(bot))
