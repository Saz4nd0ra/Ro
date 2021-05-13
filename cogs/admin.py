import discord
from discord.ext import commands
import logging
from typing import Union
from .utils import checks, exceptions
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
            document = self.bot.mongo_client.db.guilds.find_one({"_id": ctx.guild.id})

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
            self.bot.mongo_client.db.guilds.update_one({"_id": ctx.guild.id}, {"$set": {field: new_setting}})
            await ctx.embed(f"Config updated for {ctx.guild.id}.")
            


    @commands.command(name="delete_config")
    async def delete_config_command(self, ctx: commands.Context):
        """Drop (delete) the guild config."""

        if await checks.is_admin(ctx):
            self.bot.mongo_client.db.guilds.delete_one({"_id": ctx.guild.id})
            await ctx.embed(f"Deleted config for {ctx.guild.id}")
        

    @commands.command(name="gen_config")
    async def gen_config_command(self, ctx: commands.Context):
        """Generates a new config for the guild."""

        if await checks.is_admin(ctx):
            
            self.bot.mongo_client.generate_guild_config(ctx.guild.id)
            await ctx.embed(f"Config generated for {ctx.guild.id}.")

    @commands.command(name="gen_users_config")
    async def gen_users_config_command(self, ctx: commands.Context):
        """Generates a user config for every user in the current guild."""

        if await checks.is_admin(ctx):
            async for member in ctx.guild.fetch_members():
                try:
                    self.bot.mongo_client.generate_users_config(member.id)
                    log.info(f"Config generated for {member.id}|{member.name}.")
                except:
                    log.warn(
                        f"Failed to generate config for {member.id}. Config might already exist."
                    )
                    continue

            await ctx.embed("Configs successfully generated!")


def setup(bot):
    bot.add_cog(Admin(bot))
