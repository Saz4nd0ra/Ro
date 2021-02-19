import discord
import json
import os
import shutil
from discord.ext import commands
from .utils import checks
from .utils.embed import Embed
from .utils.config import Config, GuildConfig


class DevCog(commands.Cog):
    """A developer cog for testing the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()

    @checks.is_dev()
    @commands.command(name="gen_config")
    async def gen_config_command(self, ctx):
        """Generates the config for the current guild."""

        guild_config = GuildConfig(ctx.guild)

        await ctx.embed(f"Config generated for {ctx.guild.id}")

    @checks.is_dev()
    @commands.command(name="print_config")
    async def print_config_command(self, ctx, guild_id: int = None):
        """Prints the config of a server."""

        with open(f"config/guild/{ctx.guild.id if guild_id is None else guild_id}.json") as f:
            data = json.load(f)

        guild_config = json.dumps(data, indent=4)

        final_string = "```json\n"

        final_string += guild_config + "\n" + "```"

        await ctx.send(final_string)

    @checks.is_dev()
    @commands.command(name="reset_config")
    async def reset_config_command(self, ctx, guild_id: int = None):
        """Resets the config of a given server."""

        os.remove(f"config/guild/{ctx.guild.id if guild_id is None else guild_id}.json")

        shutil.copyfile(
                "config/example_guild_options.json", f"config/guild/{ctx.guild.id if guild_id is None else guild_id}.json"
            )

        await ctx.embed("File deleted and reseted")

def setup(bot):
    bot.add_cog(DevCog(bot))
