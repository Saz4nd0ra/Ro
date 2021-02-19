import discord
from discord.ext import commands
from .utils.embed import Embed
from .utils import checks
from .utils.context import Context
from .utils.config import Config, GuildConfig


class TypesNotEqual(commands.CommandError):
    pass


class Admin(commands.Cog):
    """Commands for the admins to manage the bot and the guild."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()

    @checks.is_admin()
    @commands.command(name="config")
    async def config_command(self, ctx, category: str, option: str, new_value):
        """Change the server config for your guild."""

        await ctx.embed("Config changed.")

    @config_command.error
    async def config_command_error(self, ctx, exc):
        if isinstance(exc, TypesNotEqual):
            await ctx.error("The types of the setting and your new value don't match.")


def setup(bot):
    bot.add_cog(Admin(bot))
