import discord
from discord.ext import commands
from .utils.embed import RoEmbed
import logging
from typing import Union
from .utils import checks, exceptions
from .utils.db import Connect
from .utils.context import Context
from .utils.config import Config

log = logging.getLogger("cogs.admin")


class Admin(commands.Cog):
    """Commands for the admins to manage the bot and the guild."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()

    @commands.command(name="print_config")
    async def print_config_command(self, ctx: commands.Context):
        """Prints the config for the current guild. Sends to the author in private messages."""

        if await checks.is_admin(ctx):
            document = Connect.get_document(db_name="guilds", document_id=ctx.guild.id)

            fmt = "```json\n" + str(document) + "\n```"

            await ctx.author.send(fmt)
            await ctx.embed("\N{OK HAND SIGN}")

    @commands.command(name="edit_config")
    async def edit_config_command(self, ctx: commands.Context, field, new_setting: Union[bool, int, str]):
        """Change the config from the guild.

        **Args**

            <field> The setting you want to modify, available fields are: prefix, mod_role, admin_role, automod_role.
            <new_setting> What you want your setting to be changed to.
        """

        if await checks.is_admin(ctx):
            try:
                Connect.update_field_value(
                    db_name="guilds", document_id=ctx.guild.id, field=field, new_setting=new_setting
                )
                await ctx.embed(f"Config updated for {ctx.guild.id}.")
            except exceptions.MongoError:
                raise exceptions.MongoError

    @edit_config_command.error
    async def edit_config_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.MongoError):
            await ctx.error(
                "Please check if you typed in the correct setting that you want to edit."
            )

    @commands.command(name="drop_config")
    async def delete_config_command(self, ctx: commands.Context):
        """Drop (delete) the guild config."""

        if await checks.is_admin(ctx):
            try:
                Connect.delete_document(db_name="guilds",document_id=ctx.guild.id)
                await ctx.embed(f"Deleted config for {ctx.guild.id}")
            except Exception:
                raise exceptions.GuildConfigError

    @delete_config_command.error
    async def delete_config_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.GuildConfigError):
            await ctx.error(
                "Something went wrong during deletion. Does the config even exist?"
            )

    @commands.command(name="gen_config")
    async def gen_config_command(self, ctx: commands.Context):
        """Generates a new config for the guild."""

        if await checks.is_admin(ctx):
            try:
                Connect.generate_document(db_name="guilds", document_id=ctx.guild.id)
                await ctx.embed(f"Config generated for {ctx.guild.id}.")
            except Exception:
                raise exceptions.GuildConfigError

    @gen_config_command.error
    async def gen_config_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.GuildConfigError):
            await ctx.error(
                "Something went wrong when generating the config. Does the config already exist?"
            )

    @commands.command(name="gen_users_config")
    async def gen_users_config_command(self, ctx: commands.Context):
        """Generates a user config for every user in the current guild."""

        if await checks.is_admin(ctx):
            async for member in ctx.guild.fetch_members():
                try:
                    Connect.generate_document(db_name="users", document_id=member.id)
                    log.info(f"Config generated for {member.id}|{member.name}.")
                except:
                    log.warn(
                        f"Failed to generate config for {member.id}. Config might already exist."
                    )
                    continue

            await ctx.embed("Configs successfully generated!")


def setup(bot):
    bot.add_cog(Admin(bot))
