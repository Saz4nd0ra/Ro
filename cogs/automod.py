from .utils.context import Context
from discord.ext import commands
from .utils.embed import Embed
from .utils.config import Config
from .utils.api import RedditAPI
import asyncpraw

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
            if any(x in message.content for x in REDDIT_DOMAINS):
                reddit_url = message.content
                submission = await self.reddit.get_submission_from_url(reddit_url)
                if submission.over_18 and not message.channel.is_nsfw():
                    await message.delete()
                    await ctx.error(
                        f"{message.author.mention} this channel doesn't allow NSFW.", 10
                    )
                else:
                    await message.delete()
                    await ctx.send(embed=await self.reddit.send_embed(ctx, submission))
                    if submission.selftext > 1024:
                        ctx.send(submission.selftext)


def setup(bot):
    bot.add_cog(AutoMod(bot))
