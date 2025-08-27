from __future__ import annotations

from difflib import get_close_matches
from typing import List, Mapping

import discord
from discord.ext import commands

import config
from models import Guild
from utils import LinkButton, LinkType, QuoPaginator, discord_timestamp, truncate_string

from .Cog import Cog

class HelpCommand(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__(
            verify_checks=False,
            command_attrs={
                "cooldown": commands.CooldownMapping.from_cooldown(1, 8.0, commands.BucketType.member),
                "help": "Shows help about the bot, a command, or a category",
            },
        )

    @property
    def color(self):
        return self.context.bot.color

    async def send_bot_help(self, mapping: Mapping[Cog, List[commands.Command]]):
        ctx = self.context
        
        # Initialize pages dictionary
        pages = {}
        categories = []
        
        # Create home page with bot info
        home_embed = discord.Embed(
            color=self.color,
            title="📚 Quotient Help Menu",
            description=(
                f"Welcome to Quotient's help menu! Below you'll find all available commands.\n\n"
                f"```fix\n"
                f"Bot Statistics\n"
                f"• Servers: {len(ctx.bot.guilds):,}\n"
                f"• Users: {sum(g.member_count for g in ctx.bot.guilds):,}\n"
                f"• Commands: {len(set(ctx.bot.walk_commands())):,}\n"
                f"```\n"
                f"[`📌 Support Server`]({config.SERVER_LINK}) • "
                f"[`🎯 Invite Me`]({config.BOT_INVITE}) • "
                f"[`📜 Privacy Policy`](https://github.com/quotientbot/Quotient-Bot/wiki/privacy-policy)\n\n"
                f"Use the dropdown menu or buttons below to navigate through different command categories.\n"
                f"Type `{ctx.prefix}help <command>` for detailed info about a command.\n"
            )
        )

        # Add premium status if applicable
        guild = await Guild.get_or_none(pk=ctx.guild.id)
        if guild and guild.is_premium and guild.premium_end_time:
            home_embed.add_field(
                name="✨ Premium Status",
                value=(
                    f"```yaml\n"
                    f"Status: Active\n"
                    f"Expires: {discord_timestamp(guild.premium_end_time)}\n"
                    f"```"
                ),
                inline=False
            )

        # Add warning for non-support server members
        support_guild = ctx.bot.get_guild(ctx.bot.config.SERVER_ID)
        if not support_guild or not support_guild.get_member(ctx.author.id):
            home_embed.add_field(
                name="⚠️ Access Restricted",
                value=(
                    "You need to join our support server to use bot commands.\n"
                    f"[🔗 Click here to join Support Server]({ctx.bot.config.SERVER_LINK})"
                ),
                inline=False
            )

        # Add home page to pages dictionary
        pages["home"] = home_embed

        # Add category pages
        for cog, commands_list in mapping.items():
            if not cog or cog.qualified_name in ("Jishaku", "Developer"):
                continue

            filtered = await self.filter_commands(commands_list, sort=True)
            if not filtered:
                continue

            # Create category page
            emoji = getattr(cog, "emoji", "📌")
            cmd_count = len(filtered)
            
            # Add to categories list for dropdown
            categories.append((cog.qualified_name, emoji, cmd_count))
            
            # Create category embed
            category_embed = discord.Embed(
                color=self.color,
                title=f"{emoji} {cog.qualified_name} Commands",
                description=(
                    f"{cog.description or 'No category description provided.'}\n\n"
                    f"Use `{ctx.prefix}help <command>` for more details on a command.\n"
                )
            )

            # Add commands to category page
            commands_list = []
            for cmd in filtered:
                signature = f"{ctx.prefix}{cmd.qualified_name} {cmd.signature}".strip()
                aliases = f"[{', '.join(cmd.aliases)}]" if cmd.aliases else ""
                cmd_desc = cmd.help or "No description provided."
                if len(cmd_desc) > 100:
                    cmd_desc = cmd_desc[:97] + "..."
                
                commands_list.append(f"**⚡ {cmd.name}**")
                commands_list.append(f"```ml\n{signature}\n```")
                commands_list.append(f"{cmd_desc}")
                if aliases:
                    commands_list.append(f"*Aliases: {aliases}*")
                commands_list.append("")  # Empty line for spacing

            # Split commands into chunks for better readability
            category_embed.description += "\n\n" + "\n".join(commands_list)
            
            # Store in pages dict
            pages[f"category_{cog.qualified_name}"] = category_embed

        # Store home page
        pages["home"] = home_embed

        # Create categories overview page
        categories_embed = discord.Embed(
            color=self.color,
            title="📑 Command Categories",
            description="Select a category from the dropdown menu above or click its name below:\n\n"
        )

        for name, emoji, cmd_count in categories:
            categories_embed.description += f"{emoji} **{name}** - {cmd_count} commands\n"

        pages["categories"] = categories_embed

        # Create and start the help menu view
        from .HelpMenu import HelpView
        view = HelpView(pages, categories)
        await view.start(ctx)

    async def send_command_help(self, command):
        ctx = self.context
        embed = discord.Embed(
            title=f"Command: {command.qualified_name}",
            color=self.color
        )

        # Usage section
        usage = f"{ctx.prefix}{command.qualified_name} {command.signature}"
        embed.add_field(
            name="Usage",
            value=f"```ml\n{usage}\n```",
            inline=False
        )

        # Help text
        if command.help:
            embed.add_field(
                name="Description",
                value=command.help,
                inline=False
            )

        # Aliases if any
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )

        await ctx.send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(title="Error", description=error, color=discord.Color.red())
        await self.context.send(embed=embed)

    async def command_not_found(self, string):
        ctx = self.context
        cmds = {cmd.name for cmd in ctx.bot.commands}
        matches = get_close_matches(string, cmds, n=3, cutoff=0.6)

        if matches:
            matches_text = "\n".join(f"`{ctx.prefix}{match}`" for match in matches)
            return (
                f"Command `{string}` not found. Did you mean:\n"
                f"{matches_text}"
            )
        return f"Command `{string}` not found."

    async def subcommand_not_found(self, command, string):
        return f"Command `{command.qualified_name}` has no subcommand named `{string}`"
