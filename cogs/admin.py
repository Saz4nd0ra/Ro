import discord
from discord.ext import commands
from .utils.embed import Embed
from .utils import checks
from .utils.context import Context
from .utils.config import Config, GuildConfig
from .utils.helpers import load_config, dump_config


class TypesNotEqual(commands.CommandError):
    pass

class NoValueGiven(commands.CommandError):
    pass

class Admin(commands.Cog):
    """Commands for the admins to manage the bot and the guild."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()


def setup(bot):
    bot.add_cog(Admin(bot))
