from __future__ import annotations

import json
import os
import tempfile
import asyncio
from typing import Union, Optional, Literal
from datetime import datetime, timedelta

import discord 
from discord.ext import commands, tasks
from discord import app_commands, ui

from core import Cog, Context, Quotient
from models import Guild, PremiumTxn, User
from utils import emote

# For query types
PlanType = Literal["monthly", "lifetime"]


class PremiumPurchaseModal(ui.Modal):
    def __init__(self, bot: Quotient) -> None:
        super().__init__(title="Premium Purchase")
        self.bot = bot
    

    plan = ui.TextInput(
        label="Choose Plan",
        placeholder="Enter 'monthly' or 'lifetime'",
        style=discord.TextStyle.short,
        required=True
    )

    phone = ui.TextInput(
        label="Phone Number (for UPI)",
        placeholder="Enter your phone number",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        plan = self.plan.value.lower()
        if plan not in ('monthly', 'lifetime'):
            return await interaction.response.send_message("Invalid plan. Please choose 'monthly' or 'lifetime'.", ephemeral=True)
        
        amount = "Rs.99" if plan == "monthly" else "Rs.999"
        
        embed = discord.Embed(
            title="\U0001F389 Almost there!",  # Party popper emoji
            description=(
                "**Payment Details:**\n"
                f"Amount: {amount}\n"
                "UPI ID: `premiumbot@upi`\n\n"
                "**Steps:**\n"
                "1. Open your UPI app (GPay/PhonePe/Paytm)\n"
                f"2. Send {amount} to `premiumbot@upi`\n"
                "3. After payment, wait for confirmation\n\n"
                "Your premium will be activated within 5 minutes after payment verification!"
            ),
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Notify owner
        owner = self.bot.get_user(self.bot.config.OWNER_ID)
        if owner:
            verify_embed = discord.Embed(
                title="New Premium Purchase Request",
                description=(
                    f"**User:** {interaction.user.mention}\n"
                    f"**Plan:** {plan}\n"
                    f"**Amount:** {amount}\n" 
                    f"**Phone:** {self.phone.value}"
                ),
                color=discord.Color.yellow()
            )
            await owner.send(embed=verify_embed)


class Premium(Cog):
    """Premium features and management"""
    @commands.hybrid_group(name="premium", description="Premium related commands")
    async def premium(self, ctx: Context):
        """Premium commands"""
        if ctx.invoked_subcommand is None:
            await self._status(ctx)

    def __init__(self, bot: Quotient):
        super().__init__(bot)
        self.check_premium.start()

    def cog_unload(self):
        self.check_premium.cancel()

    @tasks.loop(hours=1)
    async def check_premium(self):
        """Check for expired premium subscriptions"""
        await self.bot.wait_until_ready()
        await self.check_premium_end()

    async def check_premium_end(self):
        """Check and update expired premium subscriptions"""
        # Get expired users and guilds
        expired_users = await User.filter(is_premium=True, premium_expire_time__lte=datetime.now())
        expired_guilds = await Guild.filter(is_premium=True, premium_end_time__lte=datetime.now())

        # Deactivate expired user premium
        for user in expired_users:
            user.is_premium = False
            user.premium_expire_time = None
            await user.save()

            # Try to notify user
            discord_user = self.bot.get_user(user.id)
            if discord_user:
                try:
                    await discord_user.send("Your premium subscription has expired.")
                except:
                    pass

        # Deactivate expired guild premium
        for guild in expired_guilds:
            guild.is_premium = False
            guild.premium_end_time = None
            guild.made_premium_by = None
            await guild.save()

            # Try to notify guild
            discord_guild = self.bot.get_guild(guild.id)
            if discord_guild and discord_guild.system_channel:
                try:
                    await discord_guild.system_channel.send("This server's premium subscription has expired.")
                except:
                    pass

    async def _status(self, ctx_or_interaction: Union[Context, discord.Interaction]):
        """Shows premium status and features"""
        # Get user and guild IDs based on context type
        if isinstance(ctx_or_interaction, Context):
            user_id = ctx_or_interaction.author.id
            guild_id = ctx_or_interaction.guild.id
            guild = ctx_or_interaction.guild
        else:
            user_id = ctx_or_interaction.user.id
            guild_id = ctx_or_interaction.guild_id
            guild = ctx_or_interaction.guild

        # Get user premium status
        user = await User.get_or_none(user_id=user_id)
        if not user:
            user = await User.create(user_id=user_id, is_premium=False)
        
        # Get guild premium status
        guild_data = await Guild.get_or_none(guild_id=guild_id)
        if not guild_data:
            guild_data = await Guild.create(guild_id=guild_id, is_premium=False)

        # Create main embed with premium information
        embed = discord.Embed(
            title="\u2728 VersatileX Premium",
            description="Upgrade to Premium to unlock powerful features and enhance your server experience!",
            color=discord.Color.gold()
        )

        # Premium Features Section
        features_text = (
            "**✨ Premium Features:**\n"
            "• Unlimited Scrims & Tournaments\n"
            "• Custom Role Reactions\n"
            "• Advanced Server Verification\n"
            "• Priority Support 24/7\n"
            "• Cancel-Claim System\n"
            "• Exclusive Premium Role\n"
            "• And much more!\n\n"
            "**💎 Premium Plans:**\n"
            "• Monthly: Rs.99/month\n"
            "• Lifetime: Rs.999 (one-time payment)\n\n"
            "**💳 Payment Methods:**\n"
            "• UPI (India)\n"
            "• International payments via support"
        )
        embed.add_field(name="Features & Pricing", value=features_text, inline=False)

        # User Status Section
        # Determine user plan type (Lifetime if premium and no expiry, Monthly if expiry present)
        if user.is_premium:
            if user.premium_expire_time:
                user_plan_type = "Monthly"
                user_expiry_text = user.premium_expire_time.strftime('%B %d, %Y')
            else:
                user_plan_type = "Lifetime"
                user_expiry_text = "Never"
        else:
            user_plan_type = "None"
            user_expiry_text = "N/A"

        user_status = (
            f"**Current Status:** {'✅ Active' if user.is_premium else '❌ Not Active'}\n"
            f"**Plan:** {user_plan_type}\n"
            f"**Expiry:** {user_expiry_text}"
        )
        embed.add_field(name="Your Premium Status", value=user_status, inline=False)

        # Server Status Section
        # Server Status Section
        # Determine server plan type similarly to user
        if guild_data.is_premium:
            if guild_data.premium_end_time:
                server_plan_type = "Monthly"
                server_expiry_text = guild_data.premium_end_time.strftime('%B %d, %Y')
            else:
                server_plan_type = "Lifetime"
                server_expiry_text = "Never"
            upgraded_by = guild.get_member(guild_data.made_premium_by).mention if guild.get_member(guild_data.made_premium_by) else 'Unknown'
            server_status_lines = [
                "**Current Status:** ✅ Active",
                f"**Plan:** {server_plan_type}",
                f"**Expiry:** {server_expiry_text}",
                f"**Upgraded by:** {upgraded_by}"
            ]
        else:
            server_status_lines = [
                "**Current Status:** ❌ Not Active",
                "Upgrade to unlock premium features for everyone in the server!",
                "**Plan:** None"
            ]

        embed.add_field(name="Server Premium Status", value="\n".join(server_status_lines), inline=False)

        # Create view with buttons
        view = discord.ui.View()
        
        # Buy Premium button
        buy_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Buy Premium",
            emoji="\U0001F48E",  # Diamond emoji
            custom_id="premium_buy"
        )
        
        # Support Server button
        support_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Support Server",
            url=self.bot.config.SERVER_LINK
        )
        
        view.add_item(buy_button)
        view.add_item(support_button)
        
        # Button callback
        async def button_callback(button_interaction: discord.Interaction):
            await button_interaction.response.send_modal(PremiumPurchaseModal(self.bot))
            
        buy_button.callback = button_callback

        if isinstance(ctx_or_interaction, Context):
            await ctx_or_interaction.send(embed=embed, view=view)
        else:
            await ctx_or_interaction.response.send_message(embed=embed, view=view)

        # Compact Plan Contents field (what's included in the plan)
        plan_contents = (
            "• Unlimited Scrims & Tournaments\n"
            "• Custom Role Reactions\n"
            "• Advanced Server Verification\n"
            "• Priority Support 24/7\n"
            "• Cancel-Claim System\n"
            "• Exclusive Premium Role"
        )

        # Send a follow-up message with plan contents when using Interaction, or a new message for Context
        try:
            contents_embed = discord.Embed(
                title="Plan Contents",
                description=plan_contents,
                color=discord.Color.gold()
            )
            if isinstance(ctx_or_interaction, Context):
                await ctx_or_interaction.send(embed=contents_embed)
            else:
                await ctx_or_interaction.followup.send(embed=contents_embed)
        except Exception:
            # Best-effort: ignore errors sending the extra contents embed
            pass

        

    @premium.group(name="revoke")
    @commands.is_owner()
    async def premium_revoke(self, ctx: Context):
        """Revoke premium features from users or servers (Owner only)"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            
    @premium_revoke.command(name="user")
    async def revoke_user(self, ctx: Context, user: discord.User):
        """
        Revoke premium from a user
        Parameters
        ----------
        user: The user to revoke premium from
        """
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send("Only bot owners can use this command!", ephemeral=True)

        user_data = await User.get_or_none(user_id=user.id)
        if not user_data or not user_data.is_premium:
            return await ctx.send(f"{user.mention} doesn't have premium.", ephemeral=True)

        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()

        view = ConfirmView()
        await ctx.send(
            f"Are you sure you want to revoke premium from {user.mention}?",
            view=view,
            ephemeral=True
        )

        await view.wait()
        if not view.value:
            return await ctx.send("Revoke cancelled.", ephemeral=True)

        try:
            # Revoke premium
            user_data.is_premium = False
            user_data.premium_end_time = None
            await user_data.save()

            # Remove premium from user's guilds
            premium_guilds = await Guild.filter(made_premium_by=user.id)
            for guild in premium_guilds:
                guild.is_premium = False
                guild.premium_end_time = None
                guild.made_premium_by = None
                await guild.save()

            await ctx.send(f"Successfully revoked premium from {user.mention}", ephemeral=True)

            # Try to notify user
            try:
                await user.send("Your premium subscription has been revoked.")
            except:
                pass

        except Exception as e:
            await ctx.send(f"An error occurred while revoking premium: {str(e)}", ephemeral=True)

    @premium_revoke.command(name="server")
    @commands.is_owner()
    async def revoke_server(self, ctx: Context, guild_id: str):
        """
        Revoke premium from a server
        Parameters
        ----------
        guild_id: The ID of the server to revoke premium from
        """
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send("Only bot owners can use this command!", ephemeral=True)

        try:
            guild_id = int(guild_id)
        except ValueError:
            return await ctx.send("Invalid server ID. Please provide a valid server ID.", ephemeral=True)

        guild_data = await Guild.get_or_none(guild_id=guild_id)
        if not guild_data or not guild_data.is_premium:
            return await ctx.send("That server doesn't have premium.", ephemeral=True)

        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()

        view = ConfirmView()
        target_guild = self.bot.get_guild(guild_id)
        guild_name = target_guild.name if target_guild else str(guild_id)
        
        await ctx.send(
            f"Are you sure you want to revoke premium from server: {guild_name}?",
            view=view,
            ephemeral=True
        )

        await view.wait()
        if not view.value:
            return await ctx.send("Revoke cancelled.", ephemeral=True)

        try:
            # Revoke premium
            guild_data.is_premium = False
            guild_data.premium_end_time = None
            guild_data.made_premium_by = None
            await guild_data.save()

            success_msg = f"Successfully revoked premium from server: {guild_name}"
            await ctx.send(success_msg, ephemeral=True)

            # Try to notify the server
            if target_guild and target_guild.system_channel:
                try:
                    await target_guild.system_channel.send("This server's premium subscription has been revoked.")
                except:
                    pass

        except Exception as e:
            await ctx.send(f"An error occurred while revoking premium: {str(e)}", ephemeral=True)

    @app_commands.command(name="backup-premium")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_slash(self, interaction: discord.Interaction):
        """Take a backup of premium data"""
        await self._backup_data(interaction)

    @app_commands.command(name="transfer-premium")
    async def transfer_slash(self, interaction: discord.Interaction, server_id: str):
        """
        Transfer premium to another server
        Parameters
        ----------
        server_id: The ID of the server to transfer premium to
        """
        await self._transfer_premium(interaction, server_id)

    @premium.command(name="activate")
    async def activate(self, ctx: Context):
        """Activate premium for this server"""
        await self._activate_premium(ctx)

    @premium.command(name="deactivate")
    async def deactivate(self, ctx: Context):
        """Deactivate premium for this server"""
        await self._deactivate_premium(ctx)
    
    @app_commands.command(name="activate-premium")
    async def activate_slash(self, interaction: discord.Interaction):
        """Activate premium for this server"""
        await self._activate_premium(interaction)
    
    @app_commands.command(name="deactivate-premium")
    async def deactivate_slash(self, interaction: discord.Interaction):
        """Deactivate premium for this server"""
        await self._deactivate_premium(interaction)

    async def _backup_data(self, ctx_or_interaction: Union[Context, discord.Interaction]):
        """Take a backup of premium data"""
        # Get guild ID based on context type
        if isinstance(ctx_or_interaction, Context):
            guild_id = ctx_or_interaction.guild.id
            send = ctx_or_interaction.send
        else:
            guild_id = ctx_or_interaction.guild_id
            send = ctx_or_interaction.response.send_message

        # Get premium data
        guild = await Guild.get_or_none(guild_id=guild_id)
        if not guild or not guild.is_premium:
            return await send("This server doesn't have premium activated.", ephemeral=True)

        # Create temp directory
        backup_dir = tempfile.mkdtemp()
        backup_file = os.path.join(backup_dir, f"premium_backup_{guild_id}.json")

        try:
            # Gather premium data
            premium_data = {
                "guild_id": guild.guild_id,
                "is_premium": guild.is_premium,
                "premium_end_time": guild.premium_end_time.isoformat() if guild.premium_end_time else None,
                "made_premium_by": guild.made_premium_by
            }

            # Write to file
            with open(backup_file, 'w') as f:
                json.dump(premium_data, f, indent=4)

            # Send file
            await send("Here's your premium data backup:", file=discord.File(backup_file))

        except Exception as e:
            await send(f"An error occurred while creating backup: {str(e)}", ephemeral=True)
        finally:
            # Clean up
            try:
                os.remove(backup_file)
                os.rmdir(backup_dir)
            except:
                pass

    async def _transfer_premium(self, ctx_or_interaction: Union[Context, discord.Interaction], server_id: str):
        """
        Transfer premium to another server
        Parameters
        ----------
        server_id: The ID of the server to transfer premium to
        """
        try:
            # Validate server ID
            guild_id = int(server_id)
        except ValueError:
            if isinstance(ctx_or_interaction, Context):
                return await ctx_or_interaction.send("Invalid server ID. Please provide a valid server ID.", ephemeral=True)
            else:
                return await ctx_or_interaction.response.send_message("Invalid server ID. Please provide a valid server ID.", ephemeral=True)

        # Get user and guild details based on context type
        if isinstance(ctx_or_interaction, Context):
            user_id = ctx_or_interaction.author.id
            current_guild = ctx_or_interaction.guild
        else:
            user_id = ctx_or_interaction.user.id
            current_guild = ctx_or_interaction.guild

        # Check if user has premium
        user = await User.get_or_none(user_id=user_id)
        if not user or not user.is_premium:
            if isinstance(ctx_or_interaction, Context):
                return await ctx_or_interaction.send("You don't have an active premium subscription to transfer.", ephemeral=True)
            else:
                return await ctx_or_interaction.response.send_message("You don't have an active premium subscription to transfer.", ephemeral=True)

        # Check target server exists and bot has access
        target_guild = self.bot.get_guild(guild_id)
        if not target_guild:
            error_msg = (
                "I couldn't find that server. Make sure:\n"
                "1. The ID is correct\n"
                "2. I'm in that server\n"
                "3. You're in that server"
            )
            if isinstance(ctx_or_interaction, Context):
                return await ctx_or_interaction.send(error_msg, ephemeral=True)
            else:
                return await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)

        # Check if target server already has premium
        target_guild_data = await Guild.get_or_none(guild_id=guild_id)
        if target_guild_data and target_guild_data.is_premium:
            if isinstance(ctx_or_interaction, Context):
                return await ctx_or_interaction.send("That server already has premium activated.", ephemeral=True)
            else:
                return await ctx_or_interaction.response.send_message("That server already has premium activated.", ephemeral=True)

        # Get source guild
        source_guild = await Guild.get_or_none(guild_id=current_guild.id)
        if not source_guild or not source_guild.is_premium:
            if isinstance(ctx_or_interaction, Context):
                return await ctx_or_interaction.send("This server doesn't have premium to transfer.", ephemeral=True)
            else:
                return await ctx_or_interaction.response.send_message("This server doesn't have premium to transfer.", ephemeral=True)

        # Check if user is the one who activated premium
        if source_guild.made_premium_by != user_id:
            if isinstance(ctx_or_interaction, Context):
                return await ctx_or_interaction.send("Only the user who activated premium can transfer it.", ephemeral=True)
            else:
                return await ctx_or_interaction.response.send_message("Only the user who activated premium can transfer it.", ephemeral=True)

        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()

        view = ConfirmView()
        msg = f"Are you sure you want to transfer premium from **{current_guild.name}** to **{target_guild.name}**?"
        
        if isinstance(ctx_or_interaction, Context):
            message = await ctx_or_interaction.send(msg, view=view, ephemeral=True)
        else:
            await ctx_or_interaction.response.send_message(msg, view=view, ephemeral=True)

        await view.wait()
        if not view.value:
            if isinstance(ctx_or_interaction, Context):
                return await ctx_or_interaction.send("Transfer cancelled.", ephemeral=True)
            else:
                return await ctx_or_interaction.followup.send("Transfer cancelled.", ephemeral=True)

        try:
            # Deactivate premium in source guild
            source_guild.is_premium = False
            source_guild.premium_end_time = None
            source_guild.made_premium_by = None
            await source_guild.save()

            # Activate premium in target guild
            if not target_guild_data:
                target_guild_data = await Guild.create(
                    guild_id=guild_id,
                    is_premium=True,
                    premium_end_time=source_guild.premium_end_time,
                    made_premium_by=user_id
                )
            else:
                target_guild_data.is_premium = True
                target_guild_data.premium_end_time = source_guild.premium_end_time
                target_guild_data.made_premium_by = user_id
                await target_guild_data.save()

            success_msg = f"Successfully transferred premium from **{current_guild.name}** to **{target_guild.name}**"
            if isinstance(ctx_or_interaction, Context):
                await ctx_or_interaction.send(success_msg, ephemeral=True)
            else:
                await ctx_or_interaction.followup.send(success_msg, ephemeral=True)

        except Exception as e:
            error_msg = f"An error occurred while transferring premium: {str(e)}"
            if isinstance(ctx_or_interaction, Context):
                await ctx_or_interaction.send(error_msg, ephemeral=True)
            else:
                await ctx_or_interaction.followup.send(error_msg, ephemeral=True)

    async def _activate_premium(self, ctx_or_interaction: Union[Context, discord.Interaction]):
        """Activates premium for the current server"""
        # Get user and guild based on context/interaction
        # prefer interaction.user when available, else use context.author
        if hasattr(ctx_or_interaction, 'user') and getattr(ctx_or_interaction, 'user') is not None:
            user_id = ctx_or_interaction.user.id
        else:
            user_id = ctx_or_interaction.author.id

        # guild - for Interaction use guild, for Context use guild attribute
        guild = getattr(ctx_or_interaction, 'guild', None) or getattr(ctx_or_interaction, 'guild', None)

        # message sending helpers
        if hasattr(ctx_or_interaction, 'response') and getattr(ctx_or_interaction, 'response') is not None:
            send = ctx_or_interaction.response.send_message
            followup_send = ctx_or_interaction.followup.send
        else:
            send = ctx_or_interaction.send
            followup_send = ctx_or_interaction.send
        
        # Check if user has premium
        user = await User.get_or_none(user_id=user_id)
        if not user or not user.is_premium:
            msg = (
                "You don't have an active premium subscription.\n"
                "Use `/premium status` to check your premium status."
            )
            return await send(msg, ephemeral=True)

        # Check if guild exists and get its premium status
        guild_data = await Guild.get_or_none(guild_id=guild.id)
        if not guild_data:
            guild_data = await Guild.create(guild_id=guild.id)
        elif guild_data.is_premium:
            msg = (
                "This server already has premium activated.\n"
                f"Premium was activated by: {guild.get_member(guild_data.made_premium_by).mention if guild.get_member(guild_data.made_premium_by) else 'Unknown'}"
            )
            return await send(msg, ephemeral=True)

        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()

        view = ConfirmView()
        msg = f"Are you sure you want to activate premium for **{guild.name}**?"
        
        await send(msg, view=view, ephemeral=True)

        await view.wait()
        if not view.value:
            return await followup_send("Activation cancelled.", ephemeral=True)

        try:
            # Update guild premium status
            guild_data.is_premium = True
            guild_data.premium_end_time = user.premium_expire_time
            guild_data.made_premium_by = user_id
            await guild_data.save()

            success_msg = (
                f"Successfully activated premium for **{guild.name}**!\n"
                f"Premium features will be available until: {guild_data.premium_end_time.strftime('%B %d, %Y') if guild_data.premium_end_time else 'Never'}"
            )
            await followup_send(success_msg, ephemeral=True)

        except Exception as e:
            error_msg = f"An error occurred while activating premium: {str(e)}"
            await followup_send(error_msg, ephemeral=True)

    async def _deactivate_premium(self, ctx_or_interaction: Union[Context, discord.Interaction]):
        """Deactivates premium for the current server"""
        # Get user and guild for deactivation (robust to Context or Interaction)
        if hasattr(ctx_or_interaction, 'user') and getattr(ctx_or_interaction, 'user') is not None:
            user_id = ctx_or_interaction.user.id
        else:
            user_id = ctx_or_interaction.author.id

        guild = getattr(ctx_or_interaction, 'guild', None) or getattr(ctx_or_interaction, 'guild', None)

        if hasattr(ctx_or_interaction, 'response') and getattr(ctx_or_interaction, 'response') is not None:
            send = ctx_or_interaction.response.send_message
            followup_send = ctx_or_interaction.followup.send
        else:
            send = ctx_or_interaction.send
            followup_send = ctx_or_interaction.send
        
        # Check if guild exists and has premium
        guild_data = await Guild.get_or_none(guild_id=guild.id)
        if not guild_data or not guild_data.is_premium:
            return await send("This server doesn't have premium activated.", ephemeral=True)

        # Check if user is authorized to deactivate
        if guild_data.made_premium_by != user_id and not await self.bot.is_owner(ctx_or_interaction.author if isinstance(ctx_or_interaction, Context) else ctx_or_interaction.user):
            return await send("Only the user who activated premium can deactivate it.", ephemeral=True)

        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()

        view = ConfirmView()
        msg = f"Are you sure you want to deactivate premium for **{guild.name}**?"

        await send(msg, view=view, ephemeral=True)

        await view.wait()
        if not view.value:
            return await followup_send("Deactivation cancelled.", ephemeral=True)

        try:
            # Update guild premium status
            guild_data.is_premium = False
            guild_data.premium_end_time = None
            guild_data.made_premium_by = None
            await guild_data.save()

            success_msg = f"Successfully deactivated premium for **{guild.name}**"
            await followup_send(success_msg, ephemeral=True)

        except Exception as e:
            error_msg = f"An error occurred while deactivating premium: {str(e)}"
            await followup_send(error_msg, ephemeral=True)

    # Command implementations

    @premium.command(name="backup")
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx: Context):
        """Take a backup of premium data"""
        await self._backup_data(ctx)

    @premium.command(name="transfer")
    async def transfer(self, ctx: Context, server_id: str):
        """
        Transfer premium to another server
        Parameters
        ----------
        server_id: The ID of the server to transfer premium to
        """
        await self._transfer_premium(ctx, server_id)

    @app_commands.command(name="backup-premium")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_slash(self, interaction: discord.Interaction):
        """Take a backup of premium data"""
        await self._backup_data(interaction)

    @app_commands.command(name="transfer-premium")
    async def transfer_slash(self, interaction: discord.Interaction, server_id: str):
        """
        Transfer premium to another server
        Parameters
        ----------
        server_id: The ID of the server to transfer premium to
        """
        await self._transfer_premium(interaction, server_id)

    @app_commands.command(name="premium-info")
    async def info_slash(self, interaction: discord.Interaction):
        """Get detailed information about premium features and pricing"""
        embed = discord.Embed(
            title="\u2728 VersatileX Premium Features",
            description="Access exclusive features with VersatileX Premium!",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="\u2B50 Premium Features",
            value="\u2705 Unlimited Scrims\n"
                 "\u2705 Unlimited Tournaments\n"
                 "\u2705 Custom Reactions for Roles\n"
                 "\u2705 Priority Support 24/7\n"
                 "\u2705 Smart ServerVerification\n"
                 "\u2705 Cancel-Claim Panel\n"
                 "\u2705 Premium Role + more...",
            inline=False
        )

        embed.add_field(
            name="\U0001F48E Pricing",
            value="• Monthly: ₹99/month\n"
                 "• Lifetime: ₹999 (one-time)",
            inline=False
        )

        embed.add_field(
            name="💳 Payment Methods",
            value="• UPI (India)\n"
                 "• International payments - contact support",
            inline=False
        )

        # Get user and guild status
        user = await User.get_or_none(user_id=interaction.user.id)
        guild = await Guild.get_or_none(guild_id=interaction.guild_id)

        # User status
        embed.add_field(
            name="👤 Your Status",
            value="✅ Premium Active" if user and user.is_premium else "❌ No Premium",
            inline=False
        )

        # Guild status  
        embed.add_field(
            name="🏰 Server Status",
            value="✅ Premium Active" if guild and guild.is_premium else "❌ No Premium",
            inline=False
        )

        # Create view with buttons
        view = discord.ui.View()
        
        # Buy Premium button
        buy_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Buy Premium",
            emoji="\U0001F48E",  # Diamond emoji
            custom_id="premium_buy"
        )
        
        # Support Server button
        support_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Support Server",
            url=self.bot.config.SERVER_LINK
        )
        
        view.add_item(buy_button)
        view.add_item(support_button)
        
        # Button callback
        async def button_callback(button_interaction: discord.Interaction):
            await button_interaction.response.send_modal(PremiumPurchaseModal(self.bot))
            
        buy_button.callback = button_callback

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: Quotient) -> None:
    await bot.add_cog(Premium(bot))
