import discord
from discord.ext import commands
from .utils.embed import Embed
import logging
from .utils import checks
from .utils.db import Connect
from .utils.context import Context
from .utils.config import Config

log = logging.getLogger("cogs.admin")

class TypesNotEqual(commands.CommandError):
    pass

class NoValueGiven(commands.CommandError):
    pass

class Admin(commands.Cog):
    """Commands for the admins to manage the bot and the guild."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()

    @commands.command(name="edit_config")
    async def edit_config_command(self, ctx, field, new_setting):
        """Change the config from the guild."""

        if await checks.is_admin(ctx):
            Connect.update_guild_field(guild_id=ctx.guild.id, field=field, new_setting=new_setting)
            await ctx.embed(f"Config updated for {ctx.guild.id}.")



def setup(bot):
    bot.add_cog(Admin(bot))
