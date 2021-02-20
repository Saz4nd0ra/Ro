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

    @commands.command(name="config")
    async def config_command(self, ctx, category: str, option: str, val_type: str, new_value):
        """Change the server config for your guild. Available options for val_type: `bool, str, int`"""

        if val_type == "str":
            new_value = str(new_value)
        elif val_type == "int":
            new_value = int(new_value)
        elif val_type == "bool":
            new_value = bool(new_value)
        else:
            raise NoValueGiven

        json_data = await load_config(self, ctx.guild)

        if type(json_data[category][option]) == type(new_value):
            json_data[category][option] = new_value
            await dump_config(self, ctx.guild, json_data)
            await ctx.embed("Config changed.")
        else:
            raise TypesNotEqual


    @config_command.error
    async def config_command_error(self, ctx, exc):
        if isinstance(exc, TypesNotEqual):
            await ctx.error("The types of the setting and your new value don't match.")
        elif isinstance(exc, NoValueGiven):
            await ctx.error("You didn't specify a new value.")


def setup(bot):
    bot.add_cog(Admin(bot))
