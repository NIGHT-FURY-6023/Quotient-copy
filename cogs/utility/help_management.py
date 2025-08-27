from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import discord
from discord.ext import commands

from core import Cog
from models.misc.HelpAccess import HelpAccess

class HelpManagement(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def helpaccess(self, ctx):
        """Manage help command access"""
        await ctx.send_help(ctx.command)

    @helpaccess.command(name="grant")
    @commands.is_owner()
    async def grant_help_access(self, ctx, user: discord.User):
        """Grant help command access to a user"""
        await HelpAccess.update_or_create(
            user_id=user.id,
            defaults={
                "granted_by": ctx.author.id,
                "guild_id": ctx.guild.id if ctx.guild else None
            }
        )
        await ctx.success(f"Granted help access to {user.mention}")

    @helpaccess.command(name="revoke")
    @commands.is_owner()
    async def revoke_help_access(self, ctx, user: discord.User):
        """Revoke help command access from a user"""
        deleted = await HelpAccess.filter(user_id=user.id).delete()
        if deleted:
            await ctx.success(f"Revoked help access from {user.mention}")
        else:
            await ctx.error(f"{user.mention} didn't have help access")

    @helpaccess.command(name="list")
    @commands.is_owner()
    async def list_help_access(self, ctx):
        """List all users with help access"""
        users = await HelpAccess.all()
        if not users:
            return await ctx.error("No users have been granted help access")

        embed = discord.Embed(
            title="Users with Help Access",
            color=ctx.bot.color
        )

        for access in users:
            user = await self.bot.fetch_user(access.user_id)
            granted_by = await self.bot.fetch_user(access.granted_by) if access.granted_by else "Unknown"
            embed.add_field(
                name=f"{user} ({user.id})",
                value=f"Granted by: {granted_by}\nGranted at: {access.granted_at.strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )

        await ctx.send(embed=embed)

    @helpaccess.command(name="createrole")
    @commands.is_owner()
    @commands.has_permissions(manage_roles=True)
    async def create_help_role(self, ctx):
        """Create the 'Help Access' role in the server"""
        if discord.utils.get(ctx.guild.roles, name="Help Access"):
            return await ctx.error("Help Access role already exists")

        role = await ctx.guild.create_role(
            name="Help Access",
            color=discord.Color.blue(),
            reason="Role for help command access"
        )
        await ctx.success(f"Created {role.mention} role")

async def setup(bot: Quotient):
    await bot.add_cog(HelpManagement(bot))
