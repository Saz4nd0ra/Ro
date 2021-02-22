import discord
import json
import os
import shutil
from discord.ext import commands
from .utils import checks
from .utils.embed import Embed
from .utils.config import Config


class DevCog(commands.Cog):
    """A developer cog for testing."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()

def setup(bot):
    bot.add_cog(DevCog(bot))
