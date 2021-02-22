import discord
from discord.ext import commands
from .utils.embed import Embed
import logging
from .utils import checks
from .utils.db import Connect
from .utils.context import Context
from .utils.config import Config

log = logging.getLogger("cogs.admin")


class TypesNotEqual(commands.CommandError):
    pass


class NoValueGiven(commands.CommandError):
    pass


class GuildConfigError(commands.CommandError):
    pass


class Admin(commands.Cog):
    """Commands for the admins to manage the bot and the guild."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()

    @commands.command(name="edit_config")
    async def edit_config_command(self, ctx, field, new_setting):
        """Change the config from the guild."""

        if await checks.is_admin(ctx):
            try:
                Connect.update_guild_field(
                    guild_id=ctx.guild.id, field=field, new_setting=new_setting
                )
                await ctx.embed(f"Config updated for {ctx.guild.id}.")
            except Exception:
                raise GuildConfigError

    @edit_config_command.error
    async def edit_config_command_error(self, ctx, exc):
        if isinstance(exc, GuildConfigError):
            await ctx.error(
                "Something went wrong with editing the guild config. Does the config exist?"
            )

    @commands.command(name="drop_config")
    async def delete_config_command(self, ctx):
        """Drop (delete) the guild config."""

        if await checks.is_admin(ctx):
            try:
                Connect.delete_guild_document(ctx.guild.id)
                await ctx.embed(f"Deleted config for {ctx.guild.id}")
            except Exception:
                raise GuildConfigError

    @delete_config_command.error
    async def delete_config_command_error(self, ctx, exc):
        if isinstance(exc, GuildConfigError):
            await ctx.error(
                "Something went wrong during deletion. Does the config even exist?"
            )

    @commands.command(name="gen_config")
    async def gen_config_command(self, ctx):
        """Generates a new config for the guild."""

        if await checks.is_admin(ctx):
            try:
                Connect.generate_guild_document(ctx.guild.id)
                await ctx.embed(f"Config generated for {ctx.guild.id}.")
            except Exception:
                raise GuildConfigError

    @gen_config_command.error
    async def gen_config_command_error(self, ctx, exc):
        if isinstance(exc, GuildConfigError):
            await ctx.error(
                "Something went wrong when generating the config. Does the config already exist?"
            )

    @commands.command(name="gen_users_config")
    async def gen_users_config_command(self, ctx):
        """Generates a user config for every user in the current guild."""

        if await checks.is_admin(ctx):
            async for member in ctx.guild.fetch_members():
                try:
                    Connect.generate_user_document(user_id=member.id)
                    log.info(f"Config generated for {member.id}|{member.name}.")
                except:
                    log.warn(
                        f"Failed to generate config for {member.id}. Config might already exist."
                    )
                    continue

            await ctx.embed("Configs successfully generated!")


def setup(bot):
    bot.add_cog(Admin(bot))
