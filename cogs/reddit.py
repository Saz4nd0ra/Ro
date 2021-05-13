from .utils.context import Context
import discord
import humanize
import datetime
from discord.ext import commands
from .utils import checks 
from .utils.embed import RoEmbed
from .utils.api import RedditAPI
from .utils.config import Config

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]  # need to find more domains, if there are any


# This will return later
# I promise
# ...


class Reddit(commands.Cog):
    """Browse reddit. There isn't really a lot to it."""

    def __init__(self, bot):
        self.bot = bot
        self.api = RedditAPI()
        self.config = Config()

    @commands.command(name="redditor")
    async def redditor_command(self, ctx: commands.Context, *,name: str = None):
        """Display a redditors profile using their name."""
        if name is None:
            name = self.bot.mongo_client.db.users.find_one({"_id": ctx.author.id})["reddit_name"]
        try:
            user = await self.api.get_redditor(redditor_name=name)
        except ValueError:
            await ctx.error("Redditor not found.")

        date = humanize.naturaldate(datetime.datetime.fromtimestamp(user.created_utc))  

        if getattr(user, "is_suspended", False):
            embed = RoEmbed(
                ctx, title=f"u/{user.name}", description="This user is suspended."
            )
        else:
            embed = RoEmbed(
                ctx,
                title=f"u/{user.name}",
                thumbnail=user.icon_img,
                url=f"https://reddit.com/u/{user.name}",
            )
            embed.add_fields(
                ("Comment Karma:", f"{user.comment_karma}"),
                ("Post Karma:", f"{user.link_karma}"),
                ("Created at:", f"{date}"),
                ("Is verified:", "Yes" if user.has_verified_email else "No"),
                ("Is moderator:", "Yes" if user.is_mod else "No"),
                ("Is gold:", "Yes" if user.is_gold else "No"),
            )

        await ctx.send(embed=embed)

    @commands.command(name="meme")
    async def meme_command(self, ctx: commands.Context):
        """Get a random meme from r/memes."""
        submission = await self.api.get_submission("memes", "hot")

        embed = await self.api.build_embed(ctx, submission)

        await ctx.send(embed=embed)

    @commands.command(name="embedify")
    async def embedify_command(self, ctx: commands.Context, *, url: str):
        """Embedify a reddit post. Use in case the automatic embedifier is deactivated."""
        if self.bot.mongo_client.db.guilds.find_one({"_id": ctx.guild.id})["auto_embed"]:
            await ctx.error(
                "Reddit embeds are enabled. Just share the link without using the command next time!"
            )

        submission = await self.api.get_submission_from_url(url)

        embed = await self.api.build_embed(ctx, submission)

        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(name="thighs")
    async def thighs_command(self, ctx: commands.Context):
        """Get some thighs from r/thighdeology."""

        submission = await self.api.get_submission(
            subreddit_name="thighdeology", sorting="hot"
        )

        embed = await self.api.build_embed(ctx, submission)
        if await checks.is_nsfw_channel(ctx):
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Reddit(bot))
