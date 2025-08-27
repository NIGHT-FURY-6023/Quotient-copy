"""Support Server Check decorator."""
from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

import discord
from discord.ext import commands

from core.Context import Context

if TYPE_CHECKING:
    from core.Bot import Quotient


def support_server_only():
    """A decorator that checks if the user is in the support server.
    If not, they will be prompted to join it."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            if isinstance(args[0], commands.Context):
                ctx = args[0]
                assert isinstance(ctx, Context)
                
                # Bot owner bypass
                if await ctx.bot.is_owner(ctx.author):
                    return await func(*args, **kwargs)
                
                # Get support server
                support_guild = ctx.bot.get_guild(ctx.bot.config.SERVER_ID)
                if not support_guild:
                    await ctx.send(
                        f"❌ I was unable to find the support server. Please report this to the developers.\n"
                        f"Support Server Link: {ctx.bot.config.SERVER_LINK}"
                    )
                    return
                
                # Check if user is in support server
                if not support_guild.get_member(ctx.author.id):
                    embed = discord.Embed(
                        color=discord.Color.red(),
                        title="Not in Support Server",
                        description=(
                            f"You need to join our support server to use my commands.\n\n"
                            f"[Click here to join]({ctx.bot.config.SERVER_LINK})"
                        )
                    )
                    await ctx.send(embed=embed)
                    return
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator
