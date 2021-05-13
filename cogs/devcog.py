# Parts of that cog are taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py
# Stole the code since I am too lazy to write it myself.
# If there is a problem, contact me. Kthxbye
import discord
import os
import re
import importlib
import shutil
import asyncio
import traceback
import inspect
import textwrap
import io
import sys
import copy
import logging
import subprocess
from contextlib import redirect_stdout
from discord.ext import commands
from .utils import checks

log = logging.getLogger("cogs.devcog")

class DevCog(commands.Cog):
    """A developer cog for testing."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        return [output.decode() for output in result]

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    def get_syntax_error(self, e):
        if e.text is None:
            return f"```py\n{e.__class__.__name__}: {e}\n```"
        return f"```py\n{e.text}{'^':>{e.offset}}\n{e.__class__.__name__}: {e}```"

    @commands.command(name="load")
    async def load_command(self, ctx: commands.Context, *, module):
        """Loads a module."""
        if await checks.is_dev(ctx):
            try:
                self.bot.load_extension(module)
            except commands.ExtensionError as e:
                await ctx.error(f"{e.__class__.__name__}: {e}")
            else:
                await ctx.embed("\N{OK HAND SIGN}")

    @commands.command(name="unload")
    async def unload_command(self, ctx: commands.Context, *, module):
        """Unloads a module."""
        if await checks.is_dev(ctx):
            try:
                self.bot.unload_extension(module)
            except commands.ExtensionError as e:
                await ctx.error(f"{e.__class__.__name__}: {e}")
            else:
                await ctx.embed("\N{OK HAND SIGN}")

    @commands.group(name="reload", invoke_without_command=True)
    async def reload_command(self, ctx: commands.Context, *, module):
        """Reloads a module."""
        if await checks.is_dev(ctx):
            try:
                self.bot.reload_extension(module)
            except commands.ExtensionError as e:
                await ctx.error(f"{e.__class__.__name__}: {e}")
            else:
                await ctx.embed("\N{OK HAND SIGN}")

    @reload_command.command(name="all")
    async def reload_all_command(self, ctx):
        """Reloads all modules."""
        if await checks.is_dev(ctx):
            reloaded_extensions = 0
            for extension in self.bot.initial_extensions:
                try:
                    self.bot.reload_extension(extension)
                    log.info(f"Reloaded {extension}")
                    reloaded_extensions += 1
                except:
                    pass
            await ctx.embed(f"Reloaded {reloaded_extensions} extensions.")

    _GIT_PULL_REGEX = re.compile(r"\s*(?P<filename>.+?)\s*\|\s*[0-9]+\s*[+-]+")

    def find_modules_from_git(self, output):
        files = self._GIT_PULL_REGEX.findall(output)
        ret = []
        for file in files:
            root, ext = os.path.splitext(file)
            if ext != ".py":
                continue

            if root.startswith("cogs/"):
                # A submodule is a directory inside the main cog directory for
                # my purposes
                ret.append((root.count("/") - 1, root.replace("/", ".")))

        # For reload_command order, the submodules should be reloaded first
        ret.sort(reverse=True)
        return ret

    def reload_or_load_extension(self, module):
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionNotLoaded:
            self.bot.load_extension(module)

    @commands.command(name="update")
    async def update_command(self, ctx):
        """Updates all modules."""

        if await checks.is_dev(ctx):
            async with ctx.typing():
                stdout, stderr = await self.run_process("git pull")

            # progress and stuff is redirected to stderr in git pull
            # however, things like "fast forward" and files
            # along with the text "already up-to-date" are in stdout

            if stdout.startswith("Already up-to-date."):
                return await ctx.embed(stdout)
            
            reload_all_command = self.bot.get_command("reload all")

            await ctx.invoke(reload_all_command)

    @commands.command(name="eval")
    async def eval_command(self, ctx: commands.Context, *, body: str):
        """Evaluates a code"""
        if await checks.is_dev(ctx):
            env = {
                "bot": self.bot,
                "ctx": ctx,
                "channel": ctx.channel,
                "author": ctx.author,
                "guild": ctx.guild,
                "message": ctx.message,
                "_": self._last_result
            }

            env.update(globals())

            body = self.cleanup_code(body)
            stdout = io.StringIO()

            to_compile = f"async def func():\n{textwrap.indent(body, '  ')}"
            try:
                exec(to_compile, env)
            except Exception as e:
                return await ctx.embed(f"```py\n{e.__class__.__name__}: {e}\n```")

            func = env["func"]
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = stdout.getvalue()
                await ctx.embed(f"```py\n{value}{traceback.format_exc()}\n```")
            else:
                value = stdout.getvalue()
                try:
                    await ctx.message.add_reaction("\u2705")
                except:
                    pass

                if ret is None:
                    if value:
                        await ctx.embed(f"```py\n{value}\n```")
                else:
                    self._last_result = ret
                    await ctx.embed(f"```py\n{value}{ret}\n```")

    @commands.command(name="repl")
    async def repl_command(self, ctx):
        """Launches an interactive REPL session."""
        if await checks.is_dev(ctx):
            variables = {
                "ctx": ctx,
                "bot": self.bot,
                "message": ctx.message,
                "guild": ctx.guild,
                "channel": ctx.channel,
                "author": ctx.author,
                "_": None,
            }

            if ctx.channel.id in self.sessions:
                await ctx.error("Already running a REPL session in this channel. Exit it with `quit`.")
                return

            self.sessions.add(ctx.channel.id)
            await ctx.embed("Enter code to execute or evaluate. `exit()` or `quit` to exit.")

            def check(m):
                return m.author.id == ctx.author.id and \
                    m.channel.id == ctx.channel.id and \
                    m.content.startswith("`")

            while True:
                try:
                    response = await self.bot.wait_for("message", check=check, timeout=10.0 * 60.0)
                except asyncio.TimeoutError:
                    await ctx.embed("Exiting REPL session.")
                    self.sessions.remove(ctx.channel.id)
                    break

                cleaned = self.cleanup_code(response.content)

                if cleaned in ("quit", "exit", "exit()"):
                    await ctx.embed("Exiting.")
                if cleaned.count("\n") == 0:
                    # single statement, potentially "eval"
                    try:
                        code = compile(cleaned, "<repl session>", "eval")
                    except SyntaxError:
                        pass
                    else:
                        executor = eval

                if executor is exec:
                    try:
                        code = compile(cleaned, "<repl session>", "exec")
                    except SyntaxError as e:
                        await ctx.error(self.get_syntax_error(e))
                        continue

                variables["message"] = response

                fmt = None
                stdout = io.StringIO()

                try:
                    with redirect_stdout(stdout):
                        result = executor(code, variables)
                        if inspect.isawaitable(result):
                            result = await result
                except Exception as e:
                    value = stdout.getvalue()
                    fmt = f"```py\n{value}{traceback.format_exc()}\n```"
                else:
                    value = stdout.getvalue()
                    if result is not None:
                        fmt = f"```py\n{value}{result}\n```"
                        variables["_"] = result
                    elif value:
                        fmt = f"```py\n{value}\n```"

                try:
                    if fmt is not None:
                        if len(fmt) > 2000:
                            await ctx.error("Content too big to be printed.")
                        else:
                            await ctx.send(fmt)
                except discord.Forbidden:
                    pass
                except discord.HTTPException as e:
                    await ctx.error(f"Unexpected error: `{e}`")



def setup(bot):
    bot.add_cog(DevCog(bot))
