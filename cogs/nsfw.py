from discord.ext import commands
from .utils import checks
from .utils.embed import Embed
from .utils.config import Config
from .utils.api import Rule34API
from .utils.db import Connect


class NSFW(commands.Cog):
    """Commands for degenerates. Please stick to the rules."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.rule34 = Rule34API(bot)

    @commands.group(name="r34tags")
    async def r34tags_command(self, ctx):
        """Manage your r34 tags."""
        if ctx.invoked_subcommand == None:
            try:
                current_tags = Connect.get_user_field_value(user_id=ctx.author.id, field="r34_tags")
            except:
                Connect.generate_user_document(user_id=ctx.author.id)
            finally:
                current_tags = Connect.get_user_field_value(user_id=ctx.author.id, field="r34_tags")

            await ctx.author.send(f"Your current tags are: {current_tags}")
    
    @r34tags_command.command(name="edit")
    async def r34tags_edit_command(self, ctx, action: str, *, tag: str):
        """Edit your r34tags by adding or removing tags.
        FYI: blacklisting a tag works by adding a "-" to the tag, for example: -tag1 -tag2."""
        if action == "add":
            current_tags = Connect.get_user_field_value(user_id=ctx.author.id, field="r34_tags")
            new_tags = current_tags + tag + " "
            Connect.update_user_field(user_id=ctx.author.id, field="r34_tags", new_setting=new_tags.replace("  ", " "))
        elif action == "remove":
            current_tags = Connect.get_user_field_value(user_id=ctx.author.id, field="r34_tags")
            new_tags = current_tags.replace(tag, "")
            Connect.update_user_field(user_id=ctx.author.id, field="r34_tags", new_setting=new_tags.replace("  ", " "))
        else:
            await ctx.error("Wrong action. Action must be add or remove.")

        current_tags = Connect.get_user_field_value(user_id=ctx.author.id, field="r34_tags")

        await ctx.author.send(f"Your current tags are: {current_tags}")

    @r34tags_command.command(name="delete")
    async def r34tags_delete_command(self, ctx):
        """Delete your current r34tags."""
        Connect.update_user_field(user_id=ctx.author.id, field="r34_tags", new_setting="")
        current_tags = Connect.get_user_field_value(user_id=ctx.author.id, field="r34_tags")

        await ctx.author.send(f"Your current tags are: {current_tags}")

    @commands.command(name="rule34", aliases=["r34"])
    async def rule34_command(self, ctx, *, search: str):
        """Browse rule34.xxx. Only available in NSFW channels."""
        file = await self.rule34.get_random_r34(ctx, search)

        if await checks.is_nsfw_channel(ctx):
            await ctx.send(embed=await self.rule34.build_embed(ctx, file))

    @commands.command()
    async def saucenao(self, ctx, *, url: str):
        """Get the sauce from pictures via an URL. Only available in NSFW channels."""
        pass


def setup(bot):
    bot.add_cog(NSFW(bot))
