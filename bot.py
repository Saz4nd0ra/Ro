from discord.ext import commands
import discord
from cogs.utils import context
from cogs.utils.config import Config
import datetime
import json
import os
import click
import logging
import asyncio
import aiohttp
import traceback
import sys
import contextlib
from logging.handlers import RotatingFileHandler
from collections import deque, defaultdict

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

DESCRIPTION = """
Ro - a Discord Bot made by Saz4nd0ra
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
    "cogs.owner"
)


def call_prefix(bot, msg):
    user_id = bot.user.id
    base = [f"<@{user_id}>"]
    if msg.guild is None:
        base.append("!")
    else:
        base.append(config.default_prefix)
    return base


class Ro(commands.AutoShardedBot):
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
        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.utcnow()

        print(f"Ready: {self.user} (ID: {self.user.id})")
        log.info(f"New loging at: {(datetime.datetime.utcnow())}")
        await self.change_presence(
            activity=discord.Streaming(
                name=f"use {self.config.default_prefix}help for help",
                url="https://www.twitch.tv/commanderroot",
            )
        )

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send(
                "Sorry. This command is disabled and cannot be used."
            )
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f"In {ctx.command.qualified_name}:")
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}")
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.error(error)

    async def on_shard_resumed(self, shard_id):
        log.info(f"Shard ID {shard_id} has resumed..")
        self.resumes[shard_id].append(datetime.datetime.utcnow())

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

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


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name="discord.state")

    def filter(self, record):
        if record.levelname == "WARNING" and "referencing an unknown" in record.msg:
            return False
        return True


def setup_folders():

    if not os.path.exists("logs/"):
        os.mkdir("logs/")
        print("logs/ folder created....")


@contextlib.contextmanager
def setup_logging():
    try:
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)
        logging.getLogger("discord.state").addFilter(RemoveNoise())

        log = logging.getLogger()
        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename="logs/adb.log",
            encoding="utf-8",
            mode="w",
            maxBytes=max_bytes,
            backupCount=5,
        )
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter(
            "[{asctime}] [{levelname:<7}] {name}: {message}", dt_fmt, style="{"
        )
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


def run_bot():
    loop = asyncio.get_event_loop()
    log = logging.getLogger()
    kwargs = {
        "command_timeout": 60,
        "max_size": 20,
        "min_size": 20,
    }

    bot = Ro()
    bot.run()


@click.group(invoke_without_command=True, options_metavar="[options]")
@click.pass_context
def main(ctx):
    """Launches the bot."""
    if ctx.invoked_subcommand is None:
        setup_folders()
        loop = asyncio.get_event_loop()
        with setup_logging():
            setup_folders()
            run_bot()


if __name__ == "__main__":
    main()

