from .utils.context import Context
import discord
from discord.ext import commands
from .utils import checks, exceptions
from .utils.embed import Embed
from .utils.api import RedditAPI
from .utils.config import Config
from .utils.db import Connect

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

    @commands.group(name="redditor")
    async def redditor_command(self, ctx, *, name: str = None):
        """Display a redditors profile using their name."""
        if ctx.invoked_subcommand == None:
            if name is None:
                try:
                    name = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="reddit_name")
                except:
                    raise exceptions.UserError

            user = await self.api.get_redditor(redditor_name=name)

            if getattr(user, "is_suspended", False):
                embed = Embed(
                    ctx, title=f"u/{user.name}", description="This user is suspended."
                )
            else:
                embed = Embed(
                    ctx,
                    title=f"u/{user.name}",
                    thumbnail=user.icon_img,
                    url=f"https://reddit.com/u/{user.name}",
                )
                embed.add_fields(
                    ("Comment Karma:", f"{user.comment_karma}"),
                    ("Post Karma:", f"{user.link_karma}"),
                    ("Created at:", f"{user.created_utc}"),
                    ("Is verified:", "Yes" if user.has_verified_email else "No"),
                    ("Is moderator:", "Yes" if user.is_mod else "No"),
                    ("Is gold:", "Yes" if user.is_gold else "No"),
                )

            await ctx.send(embed=embed)

    @redditor_command.command(name="set")
    async def redditor_set_command(self, ctx, name: str):
        """Set your reddit name!"""

        try:
            Connect.update_field_value(db_name="users",document_id=ctx.author.id,field="reddit_name",new_setting=name)
            await ctx.embed("\N{OK HAND SIGN}")
        except:
            raise exceptions.MongoError

    @redditor_command.error
    async def redditor_command_error(self, ctx, exc):
        if isinstance(exc, exceptions.UserError):
            await ctx.error("You did not declare a name, and you didn't set your own name in your config.")
        elif isinstance(exc, exceptions.MongoError):
            await ctx.error("Something went wrong with the database.")

    @commands.command(name="meme")
    async def meme_command(self, ctx):
        """Get a random meme from r/memes."""
        submission = await self.api.get_submission("memes", "hot")

        embed = await self.api.build_embed(ctx, submission)

        await ctx.send(embed=embed)

    @commands.command(name="embedify")
    async def embedify_command(self, ctx, *, url: str):
        """Embedify a reddit post. Use in case the automatic embedifier is deactivated."""
        if Connect.get_field_value(db_name="guilds",document_id=ctx.guild.id,field="reddit_embed"):
            await ctx.error(
                "Reddit embeds are enabled. Just share the link without using the command next time!"
            )

        submission = await self.api.get_submission_from_url(url)

        embed = await self.api.build_embed(ctx, submission)

        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(name="thighs")
    async def thighs_command(self, ctx):
        """Get some thighs from r/thighdeology."""

        submission = await self.api.get_submission(
            subreddit_name="thighdeology", sorting="hot"
        )

        embed = await self.api.build_embed(ctx, submission)
        if await checks.is_nsfw_channel(ctx):
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Reddit(bot))
