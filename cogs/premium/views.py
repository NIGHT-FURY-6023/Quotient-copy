from __future__ import annotations

import time
from typing import TYPE_CHECKING, List

import discord

if TYPE_CHECKING:
    from core import Quotient

from models import PremiumPlan, PremiumTxn, Guild
from utils import emote
from .selectors import PlanSelector

# Default values in case config is not available
DEFAULT_PAY_LINK = "https://quotientbot.xyz/premium?txnId="


class PlanSelector(discord.ui.Select):
    def __init__(self, plans: List[PremiumPlan]):
        options = []
        for plan in plans:
            options.append(
                discord.SelectOption(
                    label=f"{plan.name} - ₹{plan.price}",
                    description=plan.description,
                    value=str(plan.id),
                    emoji="💎"
                )
            )
            
        super().__init__(
            placeholder="Select a Quotient Premium Plan...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.view.plan = self.values[0]
        self.view.stop()


class PremiumPurchaseBtn(discord.ui.Button):
    def __init__(self, label="Get Quotient Pro", emoji=emote.diamond, style=discord.ButtonStyle.grey):
        super().__init__(style=style, label=label, emoji=emoji, custom_id="premium_purchase_btn")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Check if user's server is eligible (they must be admin)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send(
                "❌ Only server administrators can purchase premium!",
                ephemeral=True
            )

        # Check if server already has active premium
        guild = await Guild.get(guild_id=interaction.guild.id)
        if guild and guild.is_premium and guild.premium_end_time and guild.premium_end_time > discord.utils.utcnow():
            return await interaction.followup.send(
                f"❌ This server already has premium until {discord.utils.format_dt(guild.premium_end_time)}!",
                ephemeral=True
            )

        # First check if there are any plans available
        plans = await PremiumPlan.all().order_by("id")
        if not plans:
            await PremiumPlan.insert_plans()
            plans = await PremiumPlan.all().order_by("id")

        # Create view with plan selector
        view = discord.ui.View(timeout=180)
        view.plan = None
        
        # Add plan selector
        view.add_item(PlanSelector(plans))
        
        # Send plan selection message
        await interaction.followup.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title="🛒 Select Premium Plan",
                description="Choose a plan that suits your needs:"
            ),
            view=view,
            ephemeral=True
        )
        
        # Wait for selection
        await view.wait()
        if not view.plan:
            return await interaction.followup.send(
                "❌ Time's up! Please try again.",
                ephemeral=True
            )
            
        # Create transaction
        txn = await PremiumTxn.create(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id,
            plan_id=view.plan.id,
            amount=view.plan.price,
            payment_status="pending",
            txnid=f"QUO{int(time.time())}"
        )
        
        # Show UPI payment info
        upi_id = getattr(interaction.client.config, "UPI_ID", None)
        if not upi_id:
            return await interaction.followup.send(
                "❌ UPI payments are not configured! Please contact support.",
                ephemeral=True
            )
            
        embed = discord.Embed(
            title="💳 Complete Your Payment",
            description=(
                f"**Selected Plan:** {view.plan.name}\n"
                f"**Amount:** ₹{view.plan.price}\n"
                f"**Transaction ID:** `{txn.txnid}`\n\n"
                f"Please complete your payment using the following UPI ID:\n"
                f"**`{upi_id}`**\n\n"
                "**Instructions:**\n"
                "1. Open your UPI payment app (GPay, PhonePe, Paytm etc)\n"
                "2. Send payment to the UPI ID above\n" 
                "3. Take a screenshot of the successful payment\n"
                "4. Upload the screenshot (imgur.com recommended)\n"
                "5. Click the 'Submit Proof' button below\n\n"
                "⚠️ **Important:**\n"
                "- Payment must be completed within 3 days\n"
                "- Make sure to include the transaction ID in payment remarks\n"
                "- Keep payment proof screenshot ready before submitting"
            ),
            color=discord.Color.blurple()
        )
        
        # Create view with submit proof button
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Submit Proof",
            style=discord.ButtonStyle.green,
            custom_id=f"submit_proof_{txn.id}"
        ))
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True
            )
            
        try:
            # Create transaction
            txn = await PremiumTxn.create(
                txnid=await PremiumTxn.gen_txnid(),
                user_id=interaction.user.id,
                guild_id=interaction.guild.id,
                plan_id=int(view.plan),
            )
            
            # Get plan details
            plan = await PremiumPlan.get(id=int(view.plan))
            
            # Create payment embed
            embed = discord.Embed(
                color=discord.Color.green(),
                title="🛍️ Complete Your Purchase",
                description=(
                    f"You are about to purchase **{plan.name}** for **{interaction.guild.name}**\n\n"
                    f"**Plan Details:**\n"
                    f"• Duration: {plan.description}\n"
                    f"• Price: ₹{plan.price}\n\n"
                    f"*To purchase for a different server, use `premium` command in that server.*"
                )
            )
            
            # Create payment button
            pay_view = discord.ui.View()
            pay_view.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label="Complete Payment",
                    url=f"{self.view.bot.config.PAY_LINK or DEFAULT_PAY_LINK}{txn.txnid}"
                )
            )
            
            await interaction.followup.send(
                embed=embed,
                view=pay_view,
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )


class SubmitPaymentProof(discord.ui.Modal):
    def __init__(self, txn: PremiumTxn) -> None:
        super().__init__(title="Submit Payment Proof")
        self.txn = txn
        
        self.proof = discord.ui.TextInput(
            label="Screenshot URL",
            placeholder="Paste the link to your payment screenshot here",
            required=True,
            style=discord.TextStyle.short,
        )
        self.add_item(self.proof)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Update transaction with proof
        await PremiumTxn.filter(id=self.txn.id).update(
            payment_proof=self.proof.value,
            payment_status="pending_verification"
        )
        
        # Send verification request to admin channel
        admin_channel = interaction.client.get_channel(getattr(interaction.client.config, 'PREMIUM_CHANNEL', None))
        if admin_channel:
            embed = discord.Embed(
                title="New Premium Purchase Verification",
                description=(
                    f"**User:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Server:** {interaction.guild.name} (`{interaction.guild.id}`)\n"
                    f"**Plan:** {self.txn.plan_id}\n"
                    f"**Transaction ID:** `{self.txn.txnid}`\n"
                    f"**Proof:** [Click here]({self.proof.value})"
                ),
                color=discord.Color.yellow()
            )
            
            verify_view = VerifyPaymentView(self.txn)
            msg = await admin_channel.send(embed=embed, view=verify_view)
            
            # Store verification message ID
            await PremiumTxn.filter(id=self.txn.id).update(verification_message_id=msg.id)
            
        await interaction.followup.send(
            "✅ Your payment proof has been submitted! Please wait for verification from an admin.",
            ephemeral=True
        )

class VerifyPaymentView(discord.ui.View):
    def __init__(self, txn: PremiumTxn):
        super().__init__(timeout=None)
        self.txn = txn

    @discord.ui.button(label="Verify Payment", style=discord.ButtonStyle.green)
    async def verify_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Only admins can verify payments!", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        
        # Update transaction
        await PremiumTxn.filter(id=self.txn.id).update(
            payment_status="verified",
            payment_verified_by=interaction.user.id,
            completed_at=discord.utils.utcnow()
        )
        
        # Get plan duration
        plan = await PremiumPlan.get(id=self.txn.plan_id)
        expires_at = discord.utils.utcnow() + plan.duration
        
        # Update guild premium status
        await Guild.filter(guild_id=self.txn.guild_id).update(
            is_premium=True,
            premium_end_time=expires_at
        )
        
        # Notify user
        user = interaction.client.get_user(self.txn.user_id)
        if user:
            try:
                await user.send(
                    f"🎉 Your premium purchase has been verified! Your server now has premium access until {discord.utils.format_dt(expires_at)}."
                )
            except discord.HTTPException:
                pass
                
        # Update verification message
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "Premium Purchase Verified ✅"
        embed.add_field(name="Verified By", value=f"{interaction.user.mention} (`{interaction.user.id}`)")
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.followup.send("✅ Payment verified successfully!", ephemeral=True)

class PremiumView(discord.ui.View):
    def __init__(self, bot: Quotient, text="This feature requires Quotient Premium.", *, label="Get Quotient Pro"):
        super().__init__(timeout=None)
        self.bot = bot
        self.text = text
        self.add_item(PremiumPurchaseBtn(label=label))

    @property
    def premium_embed(self) -> discord.Embed:
        embed = discord.Embed(
            color=self.bot.color if hasattr(self.bot, 'color') else 0x00FFB3,
            title="✨ Premium Feature Discovered",
            description=(
                f"*{self.text}*\n\n"
                "**Quotient Pro Benefits:**\n"
                f"{emote.check} Unlimited Scrims & Tournaments\n"
                f"{emote.check} Custom Registration Reactions\n" 
                f"{emote.check} Advanced SSverification\n"
                f"{emote.check} Cancel-Claim System\n"
                f"{emote.check} Priority Support\n"
                f"{emote.check} Premium Role & Badge\n"
                f"{emote.check} Early Access to New Features\n"
                f"{emote.check} And much more!\n\n"
                "*Click the button below to get Quotient Pro*"
            )
        )
        return embed
