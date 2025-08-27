from __future__ import annotations

import discord
from models.misc import PremiumPlan

class PlanSelector(discord.ui.Select):
    def __init__(self, plans: list[PremiumPlan]):
        self.plans = {p.id: p for p in plans}
        
        options = []
        for plan in plans:
            options.append(
                discord.SelectOption(
                    label=plan.name,
                    description=f"₹{plan.price} for {plan.duration.days} days",
                    value=str(plan.id),
                    emoji="💎"
                )
            )
            
        super().__init__(
            placeholder="Select a premium plan...",
            options=options,
            min_values=1,
            max_values=1
        )
        
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Store selected plan
        plan_id = int(self.values[0])
        self.view.plan = self.plans[plan_id]
        
        # Stop view
        self.view.stop()
