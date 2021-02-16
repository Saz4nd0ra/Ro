from .utils.context import Context
from discord.ext import commands
from .utils.embed import Embed
from .utils.config import Config
import asyncpraw

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]


class Reddit:
    def __init__(self):
        self.config = Config()
        self.reddit = asyncpraw.Reddit(
            client_id=self.config.praw_clientid,
            client_secret=self.config.praw_secret,
            password=self.config.praw_password,
            username=self.config.praw_username,
            user_agent="another-discord-bot by /u/Saz4nd0ra",
        )

    async def get_submission_from_url(self, reddit_url: str):
        submission = await self.reddit.submission(url=reddit_url)
        return submission

    async def send_embed(self, ctx, submission):
        """Embed that doesn't include a voting system."""

        # napkin math
        downvotes = int(
            ((submission.ups / (submission.upvote_ratio * 100)) * 100) - submission.ups
        )

        VIDEO_URL = "v.redd.it"
        IMAGE_URL = "i.redd.it"

        if VIDEO_URL in submission.url:
            if hasattr(submission, "preview"):
                preview_image_link = submission.preview["images"][0]["source"]["url"]
                embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link)
            else:
                preview_image_link = "https://imgur.com/MKnguLq.png"
            embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link)
        elif IMAGE_URL in submission.url:
            embed = Embed(ctx, title=submission.title, image=submission.url)
        else:
            embed = Embed(ctx, title=submission.title)
            embed.add_field(
                name="Text:",
                value=submission.selftext
                if len(submission.selftext) <= 1024
                else "This post is too long to fit in an Embed.",
                inline=False
            )

        embed.add_fields(
            ("Upvotes <:upvote:754073992771666020>:", f"{submission.ups}"),
            ("Downvotes <:downvote:754073959791722569>:", f"{downvotes}"),
            #("Comments :envelope::", f"{}"),
            ("Author :keyboard::",f"[u/{submission.author.name}](https://reddit.com/u/{submission.author.name})"),
            ("Link :link::", f"[{submission.shortlink}]({submission.shortlink})"),
        )

        await ctx.send(embed=embed)


class AutoMod(commands.Cog):
    """A cog to do stuff automagically!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.reddit = Reddit()

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
                    await self.reddit.send_embed(ctx, submission)


def setup(bot):
    bot.add_cog(AutoMod(bot))
