from __future__ import annotations

from core import Cog, Quotient
from .commands import Premium 
from .expire import deactivate_premium, extra_guild_perks, remind_guild_to_pay, remind_user_to_pay
from .views import PremiumPurchaseBtn, PremiumView
from models import PremiumPlan
import discord

__all__ = ("setup",)


class PremiumCog(Cog, name="Premium"):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.hook = None
        if hasattr(self.bot, 'config') and hasattr(self.bot.config, 'PUBLIC_LOG'):
            self.hook = discord.Webhook.from_url(self.bot.config.PUBLIC_LOG, session=self.bot.session)
        self.premium_role_id = getattr(self.bot.config, 'PREMIUM_ROLE', None) if hasattr(self.bot, 'config') else None
        
    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def grant(self, ctx: Context):
        """Owner command to manage premium grants"""
        await ctx.send_help(ctx.command)
        
    @grant.command(name="user")
    @commands.is_owner()
    async def grant_user(self, ctx: Context, user: discord.User, duration: str):
        """Grant premium to a user for specified duration (e.g., 30d, 1m, etc)"""
        try:
            seconds = int(strtime(duration))
            if seconds < 86400:  # minimum 1 day
                return await ctx.error("Duration must be at least 1 day")
        except ValueError:
            return await ctx.error("Invalid duration format. Use something like: 30d, 1m, etc")
            
        expire_time = datetime.now(tz=IST) + timedelta(seconds=seconds)
        
        # Update user premium status
        await User.update_or_create(
            user_id=user.id,
            defaults={
                "is_premium": True,
                "premium_expire_time": expire_time,
                "made_premium_by": ctx.author.id,
                "premium_granted_at": datetime.now(tz=IST),
                "premium_notified": False
            }
        )


async def setup(bot: Quotient):
    # Insert default plans if none exist
    await PremiumPlan.insert_plans()
    
    # Add persistent view
    bot.add_view(PremiumView(bot))
    
    # Add cog
    await bot.add_cog(PremiumCog(bot))
        
        # Set up expiry timer
        await self.bot.reminders.create_timer(
            expire_time,
            "user_premium",
            user_id=user.id
        )
        
        # Add premium role if in support server
        if isinstance(ctx.guild, discord.Guild) and ctx.guild.id == self.bot.config.SERVER_ID:
            member = ctx.guild.get_member(user.id)
            if member:
                try:
                    await member.add_roles(discord.Object(id=self.premium_role_id))
                except discord.HTTPException:
                    pass
        
        await ctx.success(f"Granted premium to {user.mention} until {discord_timestamp(expire_time)}")
        
        try:
            await user.send(
                f"🎉 You have been granted Quotient Premium by {ctx.author.mention}!\n"
                f"Your premium will expire on: {discord_timestamp(expire_time)}\n"
                f"Join our support server to get the premium role: {self.bot.config.SERVER_LINK if hasattr(self.bot, 'config') else 'https://discord.gg/quotient'}"
            )
        except discord.HTTPException:
            pass

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pstatus(self, ctx: Context):
        """Get your Quotient Premium status and the current server's."""
        embed = discord.Embed(color=self.bot.color)
        embed.title = "Quotient Premium Status"

        # Get user premium status
        user = await User.get_or_none(user_id=ctx.author.id)
        if not user or not user.is_premium:
            atext = "❌ Not activated"
        else:
            atext = "✅ Activated"
            if user.premium_expire_time:
                atext += f"\n> Expires: {discord_timestamp(user.premium_expire_time,'f')}"
            if getattr(user, 'premium_granted_at', None):
                atext += f"\n> Granted: {discord_timestamp(user.premium_granted_at,'f')}"
            if getattr(user, 'made_premium_by', None):
                try:
                    premium_by = await self.bot.fetch_user(user.made_premium_by)
                    atext += f"\n> Granted by: {premium_by}"
                except discord.HTTPException:
                    pass

        embed.add_field(name="User Premium", value=atext, inline=False)

        # Get guild premium status
        guild_data = await Guild.get_or_none(guild_id=ctx.guild.id)
        if not guild_data or not guild_data.is_premium:
            btext = "❌ Not activated"
        else:
            btext = "✅ Activated"
            if guild_data.premium_end_time:
                btext += f"\n> Expires: {discord_timestamp(guild_data.premium_end_time,'f')}"
            else:
                btext += "\n> Expires: Never"
                
            if getattr(guild_data, 'made_premium_by', None):
                try:
                    premium_by = await self.bot.fetch_user(guild_data.made_premium_by)
                    btext += f"\n> Granted by: {premium_by}"
                except discord.HTTPException:
                    pass

        # Create final embed with all info
        status_embed = self.bot.embed(ctx, title="Quotient Premium Status")
        status_embed.add_field(name="User Premium Status", value=atext, inline=False)
        status_embed.add_field(name="Server Premium Status", value=btext, inline=False)
        status_embed.set_thumbnail(url=ctx.guild.me.display_avatar.url)
        status_embed.set_footer(text=f"Use {ctx.prefix}premium to view premium features")
        
        if not (user and user.is_premium) and not (guild_data and guild_data.is_premium):
            status_embed.description = f"ℹ️ Want premium features? Use `{ctx.prefix}premium` to learn more!"
            
        return await ctx.send(embed=status_embed)

    @commands.hybrid_command(aliases=("perks", "pro"))
    async def premium(self, ctx: Context):
        """View Quotient Premium features and get premium access"""
        embed = discord.Embed(
            color=self.bot.color,
            title="✨ Quotient Premium",
            description=(
                "**Upgrade your server with Quotient Premium!**\n\n"
                "**🎮 Gaming Features**\n"
                f"{emote.check} Unlimited Scrims & Tournaments\n"
                f"{emote.check} Custom Registration Reactions\n"
                f"{emote.check} Advanced Slotlists & Team Management\n"
                f"{emote.check} Priority Registration Slots\n\n"
                "**🛡️ Moderation & Security**\n"
                f"{emote.check} Smart SSverification System\n"
                f"{emote.check} Advanced Auto-Moderation\n"
                f"{emote.check} Detailed Logging & Analytics\n\n"
                "**💎 Premium Exclusives**\n"
                f"{emote.check} Premium Role & Badge\n"
                f"{emote.check} Priority Support\n"
                f"{emote.check} Early Access to New Features\n"
                f"{emote.check} Custom Bot Status\n"
            )
        )
        
        # Add plan information
        plans = await PremiumPlan.all().order_by("price")
        if plans:
            embed.add_field(
                name="💳 Available Plans",
                value="\n".join(
                    f"• **{plan.name}** - ₹{plan.price}\n  {plan.description}"
                    for plan in plans
                ),
                inline=False
            )
        
        # Add quick info
        server_link = getattr(self.bot.config, 'SERVER_LINK', 'https://discord.gg/quotient')
        embed.add_field(
            name="📌 Quick Info",
            value=(
                "• Plans are server-specific\n"
                "• Instant activation after payment\n"
                "• Access to premium support\n"
                f"• Questions? Join our [Support Server]({server_link})"
            ),
            inline=False
        )
        
        # Add footer with support server link
        embed.set_footer(
            text="Use the button below to purchase premium ✨",
            icon_url=ctx.guild.me.display_avatar.url
        )
        
        # Create view with purchase button
        view = discord.ui.View(timeout=None)
        view.add_item(PremiumPurchaseBtn())
        await ctx.send(embed=embed, view=view)

    # Premium reminder task removed since all features are free

    def cog_unload(self):
        # Nothing to clean up since premium tasks are removed
        pass

    @Cog.listener()
    async def on_guild_premium_timer_complete(self, timer: Timer):
        guild_id = timer.kwargs["guild_id"]
        _g = await Guild.get_or_none(pk=guild_id)
        
        if not _g or not _g.premium_end_time == timer.expires:
            return
            
        # Reset to free version
        await Guild.filter(pk=guild_id).update(
            is_premium=False,
            premium_end_time=None,
            premium_notified=False
        )
        
        if (_ch := _g.private_ch) and _ch.permissions_for(_ch.guild.me).embed_links:
            _e = discord.Embed(
                color=discord.Color.red(), 
                title="Quotient Premium Expired", 
                description=(
                    "Your server's premium subscription has expired. "
                    "The bot will now operate in free mode with limited features.\n\n"
                    f"Join our support server for premium renewal: {config.SERVER_LINK}"
                )
            )
            await _ch.send(embed=_e)

    @Cog.listener()
    async def on_user_premium_timer_complete(self, timer: Timer):
        user_id = timer.kwargs["user_id"]
        _user = await User.get_or_none(pk=user_id)
        
        if not _user or not _user.premium_expire_time == timer.expires:
            return
            
        # Reset to free version
        await User.filter(pk=user_id).update(
            is_premium=False,
            premium_expire_time=None,
            premium_notified=False
        )
        
        # Remove premium role if in support server
        member = await self.bot.get_or_fetch_member(self.bot.server, user_id)
        if member:
            try:
                await member.remove_roles(discord.Object(id=self.premium_role_id))
            except discord.HTTPException:
                pass
                
        # Try to notify user
        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(
                "Your Quotient Premium has expired. The bot will now operate in free mode with limited features.\n"
                f"Join our support server to renew premium: {config.SERVER_LINK}"
            )
        except discord.HTTPException:
            pass


async def setup(bot: Quotient) -> None:
    await bot.add_cog(PremiumCog(bot))
