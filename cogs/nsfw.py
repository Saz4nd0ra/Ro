from discord.ext import commands
from .utils import checks
from .utils.api import Rule34API, DanbooruAPI, SauceNaoAPI
from .utils.embed import Embed
from .utils.config import Config


class NSFW(commands.Cog):
    """Commands for degenerates. Please stick to the rules."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.rule34 = Rule34API()
        self.danbooru = DanbooruAPI()
        self.saucenao = SauceNaoAPI()

    # TODO work on a blacklist system and user configs (yikes)
    @checks.is_nsfw_channel()
    @commands.command(aliases=["r34"])
    async def rule34(self, ctx, *, search: str):
        """Browse rule34.xxx. Only available in NSFW channels."""
        pass

    @checks.is_nsfw_channel()
    @commands.command()
    async def danbooru(self, ctx, *, search: str):
        """Browse danbooru.me. Only available in NSFW channels."""
        pass

    @checks.is_nsfw_channel()
    @commands.command(aliases=["sauce"])
    async def saucenao(self, ctx, *, url: str):
        """Get the sauce from pictures via an URL. Only available in NSFW channels."""
        pass


def setup(bot):
    bot.add_cog(NSFW(bot))
