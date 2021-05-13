from os import stat
from .utils.context import Context
from discord.ext import commands
import discord
import logging
from .utils.config import Config
from .utils.db import RoDBClient
from .utils.api import RedditAPI
from .utils import static

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
        self.mongo_client = RoDBClient(self.config.mongodb_url)


    def generate_configs(self, guild):
        """Generates all necessary configs upon joining a guild."""
        

    @commands.Cog.listener()
    async def on_message(self, message):
        """Catch reddit links, check them, and then return them as an embed."""
        ctx = await self.bot.get_context(message, cls=Context)
        if message.guild is not None:
            if any(x in message.content for x in REDDIT_DOMAINS) and not message.content.startswith(str(ctx.prefix)) and not "/rpan/" in message.content:
                if self.mongo_client.db.guilds.find_one({"_id": message.guild.id})["auto_embed"] == True:
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
            self.mongo_client.generate_guild_config(guild.id)
        except:
            pass
        prefix = self.mongo_client.db.guilds.find_one({"_id": guild.id})["prefix"]

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
            text="Saz4nd0ra/Ro-discord-bot",
            icon_url=static.GitHubIcon,
        )
        embed.set_author(
            name="Obligatory Welcome Message | Thanks for inviting me!",
            icon_url=static.AppIcon,
            url=static.GitHubRepo,
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
            role_id = self.mongo_client.db.guilds.find_one({"_id": member.guild.id})["newmember_role"]
        except:
            log.error("Error in guild config, either guild config isn't available or there is an error withing the bot.")

        if role_id == 0:
            return

        role = member.guild.get_role(role_id)
        await member.add_roles(role)


def setup(bot):
    bot.add_cog(AutoMod(bot))
