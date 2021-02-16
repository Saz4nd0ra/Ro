from .utils.context import Context
from discord.ext import commands
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


def setup(bot):
    bot.add_cog(Reddit(bot))
