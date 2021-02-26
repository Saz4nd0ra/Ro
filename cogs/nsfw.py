from discord.ext import commands
import aiohttp
from .utils import checks, exceptions
from .utils.embed import Embed
from .utils.config import Config
from .utils.api import Rule34API, SauceNaoAPI
from .utils.db import Connect
from .utils.exceptions import *


class NSFW(commands.Cog):
    """Commands for degenerates. Please stick to the rules."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.saucenao = SauceNaoAPI()
        self.rule34 = Rule34API(bot)

    @commands.group(name="r34tags")
    async def r34tags_command(self, ctx: commands.Context):
        """Manage your r34 tags."""
        if ctx.invoked_subcommand == None:
            try:
                current_tags = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags")
            except:
                Connect.generate_document(db_name="users",document_id=ctx.author.id)
            finally:
                current_tags = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags")

            await ctx.author.send(f"Your current tags are: {current_tags}")
    
    @r34tags_command.command(name="add")
    async def r34tags_add_command(self, ctx: commands.Context, *, tag: str):
        """Add a tag to your personal tags.
        FYI: blacklisting a tag works by adding a "-" to the tag, for example: -tag1 -tag2."""
        current_tags = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags")
        new_tags = current_tags + tag + " "
        Connect.update_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags", new_setting=new_tags.replace("  ", " "))

        current_tags = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags")

        await ctx.author.send(f"Your current tags are: {current_tags}")
        await ctx.embed("\N{OK HAND SIGN}")

    @r34tags_command.command(name="remove")
    async def r34tags_remove_command(self, ctx: commands.Context, *, tag: str):
        """Remove a tag from your personal tags.
        FYI: blacklisting a tag works by adding a "-" to the tag, for example: -tag1 -tag2."""
        current_tags = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags")
        new_tags = current_tags.replace(tag, "")
        Connect.update_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags", new_setting=new_tags.replace("  ", " "))

        current_tags = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags")

        await ctx.author.send(f"Your current tags are: {current_tags}")
        await ctx.embed("\N{OK HAND SIGN}")

    @r34tags_command.command(name="clear")
    async def r34tags_clear_command(self, ctx: commands.Context):
        """Clear your current r34tags."""
        Connect.update_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags", new_setting="")
        current_tags = Connect.get_field_value(db_name="users",document_id=ctx.author.id,field="r34_tags")

        await ctx.author.send(f"Your current tags are: {current_tags}")
        await ctx.embed("\N{OK HAND SIGN}")

    @commands.command(name="rule34", aliases=["r34"])
    async def rule34_command(self, ctx: commands.Context, *, search: str):
        """Browse rule34.xxx. Only available in NSFW channels."""

        if await checks.is_nsfw_channel(ctx):
            await ctx.send(embed=await self.rule34.build_embed(ctx, await self.rule34.get_random_r34(ctx.author.id, search)))
        else:
            await ctx.autor.send(embed=await self.rule34.build_embed(ctx, await self.rule34.get_random_r34(ctx.author.id, search)))

    @commands.command(name="saucenao")
    async def saucenao_command(self, ctx: commands.Context, url: str = None):
        """Get the sauce from pictures via an URL. Only available in NSFW channels."""
        
        if len(ctx.message.attachments) > 0:
            attachment_url = ctx.message.attachments[0].url
            data = await ctx.message.attachments[0].read()
        elif url is not None:
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as r:
                        data = await r.read()
                except aiohttp.InvalidURL:
                    return await ctx.error("That URL is invalid.")
                except aiohttp.ClientError:
                    return await ctx.error("Something went wrong while trying to get the image.")

        if await checks.is_nsfw_channel(ctx):
            await ctx.send(embed=await self.saucenao.build_embed(ctx=ctx, file=data, image_url=url if url else attachment_url))
            if ctx.message.guild:
                await ctx.message.delete()
                


def setup(bot):
    bot.add_cog(NSFW(bot))
