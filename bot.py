from discord.ext import commands
import discord
from cogs.utils import context
from cogs.utils.db import Connect
from cogs.utils.config import Config
from cogs.utils import time
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

config = Config()

initial_extensions = (
    "cogs.general",
    "cogs.mod",
    "cogs.music",
    "cogs.nsfw",
    "cogs.reddit",
    "cogs.automod",
    "cogs.devcog",
    "cogs.admin",
)


def call_prefix(bot, msg):
    user_id = bot.user.id
    base = [f"<@{user_id}>"]
    if msg.guild is None:
        base.append("!")
    else:
        base.append(config.default_prefix)
        try:
            base.append(Connect.get_field_value(db_name="guilds",document_id=msg.guild.id,field="prefix"))
        except:
            pass
    return base


class ADB(commands.AutoShardedBot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(
            roles=False, everyone=False, users=True
        )
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
        )
        super().__init__(
            command_prefix=call_prefix,
            description=DESCRIPTION,
            pm_help=None,
            help_attrs=dict(hidden=True),
            fetch_offline_members=True,
            heartbeat_timeout=150.0,
            allowed_mentions=allowed_mentions,
            intents=intents,
        )

        self.config = config
        self.session = aiohttp.ClientSession(loop=self.loop)

        self._prev_events = deque(maxlen=10)

        self.resumes = defaultdict(list)
        self.identifies = defaultdict(list)

        self.initial_extensions = initial_extensions

        for extension in self.initial_extensions:
            try:
                self.load_extension(extension)
                log.info(f"Loaded {extension}..")
            except Exception as e:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print(f"Ready: {self.user} (ID: {self.user.id})")
        log.info(f"New loging at: {(datetime.datetime.utcnow())}")
        await self.change_presence(
            activity=discord.Streaming(
                name=f"use {self.config.default_prefix}help for help!",
                url="https://www.twitch.tv/commanderroot",
            )
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send(
                "Sorry. This command is disabled and cannot be used."
            )
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}", file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)

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
