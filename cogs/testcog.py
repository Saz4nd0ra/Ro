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
        embed.add_field(
            name="Now Playing:\n",
            value=f"[{player.queue.current_track.title}]({player.queue.current_track.uri}) | Requested by: {player.queue.current_track.requester.name}\n",
            inline=False,
        )
        if len(final_string) == 0:
            pass
        else:
            embed.add_field(
                name="Up next:\n",
                value="".join(f"{string}" for string in final_string),
                inline=False,
            )

def setup(bot):
    bot.add_cog(Testcog(bot))
