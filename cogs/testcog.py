import discord
from discord.ext import commands
from .utils import checks
from .utils.embed import Embed
from .utils.config import Config, GuildConfig


class Testcog(commands.Cog):
    """A developer cog for testing the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()

    @checks.is_dev()
    @commands.command()
    async def gen_config(self, ctx):
        """Generates the config for the current guild."""

        guild_config = GuildConfig(ctx)

        await ctx.send(guild_config.guild_prefix)

        await ctx.embed(f"Config generated for {ctx.guild.id}")

def setup(bot):
    bot.add_cog(Testcog(bot))
