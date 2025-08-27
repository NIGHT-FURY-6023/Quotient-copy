from __future__ import annotations

import asyncio
import io
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, TypeVar, Union

import aiohttp
import discord
from discord.ext import commands

import config as cfg
import utils

BotT = TypeVar("BotT", bound=commands.Bot)

__all__ = ("Context",)

class Context(commands.Context["commands.Bot"], Generic[BotT]):
    if TYPE_CHECKING:
        from .Bot import Quotient

    bot: Quotient

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def db(self):
        return self.bot.db

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session

    @property
    def guild_color(self):
        return self.bot.cache.guild_color(self.guild.id)

    @property
    def config(self) -> cfg:
        return self.bot.config

    @property
    async def banlog_channel(self):
        from models import BanLog
        record = await BanLog.get_or_none(guild_id=self.guild.id)

    async def success(self, message: str, **kwargs) -> discord.Message:
        """Send a success message with green color"""
        embed = discord.Embed(color=discord.Color.green(), description=f"✅ {message}")
        
        # Try regular command context first
        if not hasattr(self, 'interaction') or not self.interaction:
            return await self.send(embed=embed, **kwargs)
            
        # Handle interaction context
        try:
            if not self.interaction.response.is_done():
                await self.interaction.response.send_message(embed=embed, **kwargs)
                return await self.interaction.original_response()
            return await self.interaction.followup.send(embed=embed, **kwargs)
        except:
            return await self.send(embed=embed, **kwargs)
