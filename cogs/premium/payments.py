from discord import app_commands
from discord.ext import commands
import discord
from core import Quotient
from models import Guild, User
import asyncio

class PremiumPayments(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    premium_group = app_commands.Group(name="premium", description="Premium related commands")
    
    @premium_group.command(name="buy")
    async def premium_buy(self, interaction: discord.Interaction):
        """Purchase premium features using UPI payment"""
        
        # Premium pricing embed
        embed = discord.Embed(
            title="VersatileX Premium",
            description="Upgrade to Premium to unlock all features!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Premium Features",
            value="✓ Unlimited Scrims\n✓ Unlimited Tournaments\n✓ Custom Reactions\n✓ Smart Serverification\n✓ Premium Role + more...",
            inline=False
        )
        
        embed.add_field(
            name="Price", 
            value="₹99/month", 
            inline=False
        )
        
        # Payment button
        class PaymentButton(discord.ui.Button):
            def __init__(self):
                super().__init__(
                    style=discord.ButtonStyle.green,
                    label="Pay with UPI",
                    emoji="💳"
                )
                
            async def callback(self, interaction: discord.Interaction):
                # Create payment modal
                class UPIModal(discord.ui.Modal, title="UPI Payment"):
                    upi_id = discord.ui.TextInput(
                        label="Enter your UPI ID",
                        placeholder="yourname@upi",
                        required=True
                    )
                    
                    async def on_submit(self, interaction: discord.Interaction):
                        # Send to verification channel visible only to bot owner
                        owner = interaction.client.owner
                        channel = interaction.client.get_channel(interaction.client.config.PAYMENT_LOGS) 
                        
                        verify_embed = discord.Embed(
                            title="New Premium Purchase",
                            description=f"User: {interaction.user.mention}\nUPI ID: {self.upi_id.value}",
                            color=discord.Color.yellow()
                        )
                        
                        # Verification buttons
                        class VerifyView(discord.ui.View):
                            @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
                            async def approve(self, i: discord.Interaction, button: discord.ui.Button):
                                if i.user.id != i.client.owner_id:
                                    return
                                
                                # Add premium
                                user = await User.get_or_create(user_id=interaction.user.id)
                                user.is_premium = True
                                await user.save()
                                
                                await interaction.user.send("Your premium purchase has been approved! You now have access to all premium features.")
                                await i.message.edit(content="Payment Verified ✅", view=None)
                                
                            @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)  
                            async def deny(self, i: discord.Interaction, button: discord.ui.Button):
                                if i.user.id != i.client.owner_id:
                                    return
                                    
                                await interaction.user.send("Your premium purchase was denied. Please try again or contact support.")
                                await i.message.edit(content="Payment Denied ❌", view=None)
                                
                        await channel.send(embed=verify_embed, view=VerifyView())
                        await interaction.response.send_message("Your payment is being verified by the bot owner. You'll receive a DM once approved!", ephemeral=True)
                
                await interaction.response.send_modal(UPIModal())
        
        view = discord.ui.View()
        view.add_item(PaymentButton())
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @premium_group.command(name="status")
    async def premium_status(self, interaction: discord.Interaction):
        """Check your premium status"""
        user = await User.get_or_none(user_id=interaction.user.id)
        
        if not user or not user.is_premium:
            embed = discord.Embed(
                title="Premium Status",
                description="❌ You don't have premium access\nUse `/premium buy` to purchase!",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="Premium Status", 
                description="✅ You have premium access!",
                color=discord.Color.green()
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command()
    @commands.is_owner()
    async def givepremium(self, ctx, user: discord.User):
        """Give premium access to a user (Bot owner only)"""
        user_model = await User.get_or_create(user_id=user.id)
        user_model.is_premium = True
        await user_model.save()
        
        await ctx.send(f"✅ Given premium access to {user.mention}")
        try:
            await user.send("🎉 You have been given premium access by the bot owner!")
        except:
            pass

async def setup(bot: Quotient):
    await bot.add_cog(PremiumPayments(bot))
