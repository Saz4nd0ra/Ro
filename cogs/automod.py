from .utils.context import Context
from discord.ext import commands
from .utils.embed import Embed
import discord
import logging
from .utils.config import Config
from .utils.api import RedditAPI
from .utils.db import Connect
from .utils.exceptions import *

log = logging.getLogger("cogs.automod")

REDDIT_DOMAINS = [
    "reddit.com",
    "redd.it",
]


class AutoMod(commands.Cog):
    """A cog to do stuff automagically!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.reddit = RedditAPI()

    def generate_configs(self, guild):
        """Generates all necessary configs upon joining a guild."""
        

    @commands.Cog.listener()
    async def on_message(self, message):
        """Catch reddit links, check them, and then return them as an embed."""
        ctx = await self.bot.get_context(message, cls=Context)
        if message.guild is not None:
            if any(x in message.content for x in REDDIT_DOMAINS) and not message.content.startswith(str(ctx.prefix)) and not "/rpan/" in message.content:
                if Connect.get_field_value(db_name="guilds", document_id=ctx.guild.id, field="reddit_embed") == True:
                    reddit_url = message.content
                    submission = await self.reddit.get_submission_from_url(reddit_url)
                    if submission.over_18 and not message.channel.is_nsfw():
                        await message.delete()
                        await ctx.error(
                            f"{message.author.mention} this channel doesn't allow NSFW.", 10
                        )
                    else:
                        await message.delete()
                        await ctx.send(embed=await self.reddit.build_embed(ctx, submission))
                        if len(submission.selftext) > 1024:
                            ctx.send(submission.selftext)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        try:
            Connect.generate_document(db_name="guilds",document_id=guild.id)
        except:
            pass
        prefix = Connect.get_field_value(db_name="guilds", document_id=guild.id, field="prefix")

        embed = discord.Embed(
            description=f"Your current Server prefix is: {prefix}\n"
            'For more help, [click here](https://discord.gg/ycUPFpy) to join the  "support" server.',
            colour=0x7289DA,
        )

        embed.add_field(
            name="For help:",
            value=f"Use {prefix}help to get an overlook of all available commands.",
        )
        embed.set_footer(
            text="Saz4nd0ra/another-discord-bot",
            icon_url="https://cdn3.iconfinder.com/data/icons/popular-services-brands/512/github-512.png",
        )
        embed.set_author(
            name="Obligatory Welcome Message | Thanks for inviting me!",
            icon_url=self.bot.user.avatar_url,
            url="https://github.com/Saz4nd0ra/another-discord-bot",
        )
        for i in range(0, len(guild.text_channels)):
            try:
                await guild.text_channels[i].send(embed=embed)
                break
            except:
                continue

    @commands.Cog.listener()
    async def on_member_join(self, member):

        try:
            role_id = Connect.get_field_value(db_name="guilds", document_id=member.guild.id, field="automod_role")
        except:
            log.error("Error in guild config, either guild config isn't available or there is an error withing the bot.")

        if role_id == 0:
            return

        role = member.guild.get_role(role_id)
        await member.add_roles(role)


def setup(bot):
    bot.add_cog(AutoMod(bot))
