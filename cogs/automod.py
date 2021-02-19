from .utils.context import Context
from discord.ext import commands
from .utils.embed import Embed
import discord
from .utils.config import Config, GuildConfig
from .utils.api import RedditAPI

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]


class AutoMod(commands.Cog):
    """A cog to do stuff automagically!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.reddit = RedditAPI()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Catch reddit links, check them, and then return them as an embed."""
        ctx = await self.bot.get_context(message, cls=Context)
        if self.config.enable_redditembed:
            if any(
                x in message.content for x in REDDIT_DOMAINS
            ) and not message.content.startswith(str(ctx.prefix)):
                reddit_url = message.content
                submission = await self.reddit.get_submission_from_url(reddit_url)
                if submission.over_18 and not message.channel.is_nsfw():
                    await message.delete()
                    await ctx.error(
                        f"{message.author.mention} this channel doesn't allow NSFW.", 10
                    )
                else:
                    await message.delete()
                    await ctx.send(embed=await self.reddit.build_embed(ctx, submission))
                    if len(submission.selftext) > 1024:
                        ctx.send(submission.selftext)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        guild_config = GuildConfig(guild)

        embed = discord.Embed(
            description=f"Your current Server prefix is: {guild_config.guild_prefix}",
            colour=0x7289DA,
        )

        embed.add_field(
            name="For help:",
            value=f"Use {guild_config.guild_prefix}help to get an overlook of all available commands.",
        )
        embed.set_footer(
            text="Saz4nd0ra/another-discord-bot",
            icon_url="https://cdn3.iconfinder.com/data/icons/popular-services-brands/512/github-512.png",
        )
        embed.set_author(
            name="Thanks for inviting me!",
            icon_url=self.bot.user.avatar_url,
            url="https://github.com/Saz4nd0ra/another-discord-bot",
        )
        await guild.text_channels[0].send(embed=embed)


def setup(bot):
    bot.add_cog(AutoMod(bot))
