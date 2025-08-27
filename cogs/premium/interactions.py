from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from models import PremiumTxn
from .views import SubmitPaymentProof

if TYPE_CHECKING:
    from core import Quotient

async def handle_premium_button_interaction(bot: Quotient, interaction: discord.Interaction):
    """Handle interactions with premium payment proof buttons"""
    
    if not interaction.custom_id.startswith("submit_proof_"):
        return
        
    try:
        txn_id = int(interaction.custom_id.split("_")[-1])
    except (ValueError, IndexError):
        return
        
    # Get transaction
    txn = await PremiumTxn.get_or_none(id=txn_id)
    if not txn:
        return await interaction.response.send_message(
            "❌ Invalid transaction! Please try purchasing premium again.",
            ephemeral=True
        )
        
    # Check if this is the transaction owner
    if interaction.user.id != txn.user_id:
        return await interaction.response.send_message(
            "❌ This transaction belongs to someone else!",
            ephemeral=True
        )
        
    # Check if proof already submitted
    if txn.payment_status != "pending":
        return await interaction.response.send_message(
            "❌ Payment proof has already been submitted for this transaction!",
            ephemeral=True
        )
        
    # Show proof submission modal
    await interaction.response.send_modal(SubmitPaymentProof(txn))
