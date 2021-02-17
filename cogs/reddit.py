from .utils.context import Context
from discord.ext import commands
import humanize
from .utils.embed import Embed
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

    @commands.command()
    async def redditor(self, ctx, *, name: str):
        """Display a redditors profile using their name."""
        user = await self.api.get_user(name)

        if user.is_suspended:
            embed = Embed(ctx, title=f"u/{user.name}", description="This user is suspended.")
        else:
            embed = Embed(ctx, title=f"u/{user.name}](https://reddit.com/u/{user.name})", thumbnail=user.icon_img)
            embed.add_fields(
                ("Comment Karma:", f"{user.comment_karma}"),
                ("Post Karma:", f"{user.link_karma}"),
                ("Created at:", f"{humanize.naturaldate(user.created_utc)}"),
                ("Is verified:", "Yes" if user.has_verified_email else "No"))

        await ctx.send(embed=embed)

    @commands.command()
    async def meme(self, ctx):
        """Get a random meme."""
        submission = await self.api.get_submission("memes", "hot")

        embed = await self.api.build_embed(ctx, submission)

        await ctx.send(embed=embed)

    @commands.command()
    async def embedify(self, ctx, * , url: str):
        """Embedify a reddit post. Use in case the automatic embedifier is deactivated."""
        if self.config.enable_redditembed == True:
            await ctx.error("Reddit embeds are enabled. Just share the link without using the command next time!", 10)
        
        submission = await self.api.get_submission_from_url(url)

        embed = await self.api.build_embed(ctx, submission)

        await ctx.send(embed=embed)

        

def setup(bot):
    bot.add_cog(Reddit(bot))
