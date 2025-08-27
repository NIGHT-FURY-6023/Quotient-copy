from __future__ import annotations

import discord
from discord.ui import Button, Select, View
from typing import Dict, List

class CategorySelect(Select):
    def __init__(self, options: List[discord.SelectOption]):
        super().__init__(
            placeholder="Select a Category",
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: HelpView = self.view
        selected = self.values[0]
        if selected.startswith("category_"):
            category = selected[9:]  # Remove "category_" prefix
            page_key = f"category_{category}"
            if page_key in view.pages:
                await interaction.response.edit_message(embed=view.pages[page_key])
                view.current_page = page_key

class HelpView(View):
    def __init__(self, pages: dict, categories: List[tuple[str, str, int]]):
        super().__init__(timeout=60)
        self.pages = pages
        self.current_page = "home"
        self.message = None
        self._setup_navigation(categories)

    async def start(self, ctx):
        self.message = await ctx.send(embed=self.pages["home"], view=self)

    def _setup_navigation(self, categories: List[tuple[str, str, int]]):
        # Add category dropdown
        options = []
        for name, emoji, cmd_count in categories:
            if name:
                options.append(discord.SelectOption(
                    label=name,
                    description=f"{cmd_count} commands",
                    emoji=emoji,
                    value=f"category_{name}"
                ))

        if options:
            self.add_item(CategorySelect(options))

        # Add home button
        home = Button(
            label="Home",
            emoji="🏠",
            style=discord.ButtonStyle.primary,
            custom_id="home",
            row=1
        )
        home.callback = self.home_callback
        self.add_item(home)

        # Add categories button
        categories = Button(
            label="All Categories",
            emoji="📑",
            style=discord.ButtonStyle.secondary,
            custom_id="categories",
            row=1
        )
        categories.callback = self.categories_callback
        self.add_item(categories)

        # Add close button
        close = Button(
            label="Close",
            emoji="✖️",
            style=discord.ButtonStyle.danger,
            custom_id="close",
            row=1
        )
        close.callback = self.close_callback
        self.add_item(close)

    async def home_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.pages["home"])
        self.current_page = "home"

    async def categories_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.pages["categories"])
        self.current_page = "categories"

    async def close_callback(self, interaction: discord.Interaction):
        await interaction.message.delete()

    def add_category_button(self, label: str, emoji: str = "📌", row: int = 2):
        button = CategoryButton(label=label, emoji=emoji)
        button.row = row

        async def category_callback(interaction: discord.Interaction):
            page_key = f"category_{label}"
            if page_key in self.pages:
                await interaction.response.edit_message(embed=self.pages[page_key])
                self.current_page = page_key

        button.callback = category_callback
        self.add_item(button)
