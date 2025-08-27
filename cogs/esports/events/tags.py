from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import re
from contextlib import suppress

import discord

import utils
from core import Cog
from models import EasyTag, TagCheck

from ..helpers import EasyMemberConverter, delete_denied_message


class TagEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener(name="on_message")
    async def on_tagcheck_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id

        # Fast cache check
        if channel_id not in self.bot.cache.tagcheck:
            return

        try:
            # Get tagcheck config
            tagcheck = await TagCheck.get_or_none(channel_id=channel_id)
            if not tagcheck:
                self.bot.cache.tagcheck.discard(channel_id)
                return

            # Get ignore role
            ignore_role = tagcheck.ignorerole
            if ignore_role and ignore_role in message.author.roles:
                return

            ctx = await self.bot.get_context(message)
            _react = True
            
            # Check for bot mentions
            if any(m.bot for m in message.mentions):
                _react = False
                with suppress(discord.HTTPException):
                    await message.reply("❌ Please mention real teammates, not bots.", delete_after=5)
                    
            # Check required mentions
            elif len(message.mentions) < tagcheck.required_mentions:
                _react = False
                with suppress(discord.HTTPException):
                    await message.reply(
                        f"❌ You need to mention {tagcheck.required_mentions} teammate{'s' if tagcheck.required_mentions > 1 else ''}.",
                        delete_after=5,
                    )

            # Find team name and handle reactions
            # Find team name and handle reactions
            team_name = utils.find_team(message)
            with suppress(discord.HTTPException):
                await message.add_reaction("✅" if _react else "❌")

            if _react:
                embed = discord.Embed(color=self.bot.color)
                players = [m.mention for m in message.mentions] if message.mentions else [message.author.mention]
                embed.description = f"**Team Name:** {team_name}\n**Players:** {', '.join(players)}"
                with suppress(discord.HTTPException):
                    await message.reply(embed=embed)

            elif tagcheck.delete_after:
                # Schedule message deletion if needed
                self.bot.loop.create_task(delete_denied_message(message, 15))
                    
        except Exception as e:
            self.bot.dispatch("error", e)  # Log any errors
            return

    # ==========================================================================================================
    # ==========================================================================================================

    @Cog.listener(name="on_message")
    async def on_eztag_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id
        if not channel_id in self.bot.cache.eztagchannels:
            return

        try:
            # Get eztag config
            eztag = await EasyTag.get_or_none(channel_id=channel_id)
            if not eztag:
                self.bot.cache.eztagchannels.discard(channel_id)
                return

            # Check ignore role
            ignore_role = eztag.ignorerole
            if ignore_role and ignore_role in message.author.roles:
                return

            ctx = await self.bot.get_context(message)

            # Find discord tags in message
            tags = set(re.findall(r"\b\d{18}\b|\b@\w+", message.content, re.IGNORECASE))
            if not tags:
                with suppress(discord.HTTPException):
                    await message.add_reaction("❌")
                    await ctx.reply(
                        "❌ No Discord tags found! You can mention teammates using:\n"
                        "• Their Discord ID\n"
                        "• @their_name\n"
                        "• @their_full_discord_tag",
                        delete_after=10,
                    )
                return

            # Convert tags to members
            members = []
            for tag in tags:
                try:
                    member = await EasyMemberConverter().convert(ctx, tag)
                    if member:
                        members.append(member)
                except commands.MemberNotFound:
                    continue

            if not members:
                with suppress(discord.HTTPException):
                    await message.add_reaction("❌")
                    await ctx.reply("❌ No valid members found from the provided tags.", delete_after=10)
                return

            # Send confirmation with tags
            with suppress(discord.HTTPException):
                await message.add_reaction("✅")
                msg = await ctx.reply(
                    embed=discord.Embed(
                        color=self.bot.color,
                        description=f"**Message:** {message.clean_content}\n**Discord Tags:** {', '.join(m.mention for m in members)}"
                    )
                )

                # Handle auto-delete if enabled
                if eztag.delete_after:
                    self.bot.loop.create_task(delete_denied_message(message, 60))
                    self.bot.loop.create_task(delete_denied_message(msg, 60))

        except Exception as e:
            self.bot.dispatch("error", e)  # Log any errors
            return

    @Cog.listener(name="on_guild_channel_delete")
    async def on_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        if not isinstance(channel, discord.TextChannel):
            return

        channel_id = channel.id

        # Delete EasyTag record
        if channel_id in self.bot.cache.eztagchannels:
            await EasyTag.filter(channel_id=channel_id).delete()
            self.bot.cache.eztagchannels.remove(channel_id)

        # Delete TagCheck record
        if channel_id in self.bot.cache.tagcheck:
            await TagCheck.filter(channel_id=channel_id).delete()
            self.bot.cache.tagcheck.remove(channel_id)
