import discord
import logging
import aiohttp
import asyncio
from discord.ext import commands
from .utils import checks, exceptions
from .utils.context import Context
from .utils.embed import Embed

log = logging.getLogger(__name__)


class Owner(commands.Cog):
    """Commands for the bot owner."""
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group(name="change")
    async def change_command(self, ctx):
        """Change the bots settings, like profile picture, user name, nick name and so on."""
        if await checks.is_owner(ctx):
            if ctx.invoked_subcommand == None:
                await ctx.send_help(ctx.command)

    @change_command.command(name="avatar")
    async def change_avatar_command(self, ctx, url: str = None):
        """Change the bots profile picture. JPGs and PNGs only!"""
        if await checks.is_owner(ctx):
            if len(ctx.message.attachments) > 0:
                data = await ctx.message.attachments[0].read()
            elif url is not None:
                if url.startswith("<") and url.endswith(">"):
                    url = url[1:-1]

                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(url) as r:
                            data = await r.read()
                    except aiohttp.InvalidURL:
                        return await ctx.error("That URL is invalid.")
                    except aiohttp.ClientError:
                        return await ctx.error("Something went wrong while trying to get the image.")
                try:
                    await ctx.bot.user.edit(avatar=data)
                    await ctx.embed("\N{OK HAND SIGN}")
                except:
                    raise exceptions.DiscordAPIError

    @change_avatar_command.error
    async def change_avatar_command_error(self, ctx, exc):
        if isinstance(exc, exceptions.DiscordAPIError):
            await ctx.error("Something went wrong. Try again but be careful to not exceed the limit.")

    @change_command.command(name="username")
    async def change_username_command(self, ctx, *, username: str):
        """Change the bots user name."""

        if await checks.is_owner(ctx):
            if len(username) > 32:
                raise exceptions.UserError
            
            try:
                await self.bot.user.edit(username=username)
                await ctx.embed("\N{OK HAND SIGN}")
            except asyncio.TimeoutError:
                raise exceptions.DiscordAPIError

    @change_username_command.error
    async def change_username_command_error(self, ctx, exc):
        if isinstance(exc, exceptions.DiscordAPIError):
            await ctx.error("Something went wrong. Try again but be careful to not exceed the limit.")

    @change_command.command(name="nickname")
    async def change_nickname_command(self, ctx, *, nickname):
        """Change the bots nickname for the current guild."""

        if await checks.is_owner(ctx):
            if len(nickname) > 32:
                raise exceptions.UserError

            try:
                await ctx.guild.me.edit(nick=nickname)
                await ctx.embed("\N{OK HAND SIGN}")
            except discord.Forbidden:
                raise exceptions.DiscordAPIError

    @change_nickname_command.error
    async def change_nickname_command_error(self, ctx, exc):
        if isinstance(exc, exceptions.UserError):
            await ctx.error("Something went wrong. Try again but be careful to not exceed the limit.")
        elif isinstance(exc, exceptions.DiscordAPIError):
            await ctx.error("Something went wrong. Are you sure that I have permission to do that?")

def setup(bot):
    bot.add_cog(Owner(bot))

