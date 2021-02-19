from discord.ext import commands
import discord
from cogs.utils import context
from cogs.utils.config import Config
import datetime
import json
import logging
import aiohttp
import traceback
import sys
from collections import deque, defaultdict

DESCRIPTION = """
another-discord-bot
"""

log = logging.getLogger(__name__)


initial_extensions = (
    "cogs.general",
    "cogs.mod",
    "cogs.music",
    "cogs.nsfw",
    "cogs.reddit",
    "cogs.automod",
    "cogs.devcog",
    "cogs.admin"
)


class ADB(commands.AutoShardedBot):
    def __init__(self, config=Config()):
        super().__init__(
            command_prefix=config.default_prefix,
            description=DESCRIPTION,
            fetch_offline_members=False,
            heartbeat_timeout=150.0,
        )
        self.config = config
        self.session = aiohttp.ClientSession(loop=self.loop)

        self._prev_events = deque(maxlen=10)

        # shard_id: List[datetime.datetime]
        # shows the last attempted IDENTIFYs and RESUMEs
        self.resumes = defaultdict(list)
        self.identifies = defaultdict(list)

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
                log.info(f"Loaded {extension}..")
            except Exception as e:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):

        log.info(f"Ready: {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Streaming(
                name=f"{self.config.default_prefix}help",
                url="https://www.twitch.tv/commanderroot",
            )
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}", file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.error(error)

    async def on_shard_resumed(self, shard_id):
        log.info(f"Shard ID {shard_id} has resumed..")
        self.resumes[shard_id].append(datetime.datetime.utcnow())

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        super().run(self.config.login_token, reconnect=True)
