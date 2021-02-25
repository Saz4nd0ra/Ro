import asyncpraw
from .config import Config
import random
import asyncio
import rule34
from discord.ext import commands
from saucenao_api import SauceNao
from .db import Connect
from .embed import Embed
from . import exceptions


VIDEO_FORMATS = [
    "mp4",
    "webm",
    "mkv"
    # and so on, I don't really know which formats r34 uses
]

class RedditAPI:
    def __init__(self):

        self.config = Config()
        self.reddit = asyncpraw.Reddit(
            client_id=self.config.praw_clientid,  # connecting to reddit using appilcation details and account details
            client_secret=self.config.praw_secret,
            password=self.config.praw_password,  # the actual password of the application account
            username=self.config.praw_username,  # the actual username of the application account
            user_agent="another-discord-bot by /u/Saz4nd0ra",
        )

    async def get_submission(self, subreddit_name: str, sorting: str):
        subreddit = await self.reddit.subreddit(subreddit_name)

        if sorting == "hot":
            submission_list = [
                submission
                async for submission in subreddit.hot(limit=20)
                if not submission.stickied
            ]
        elif sorting == "new":
            submission_list = [
                submission
                async for submission in subreddit.new(limit=20)
                if not submission.stickied
            ]
        else:
            submission_list = [
                submission
                async for submission in subreddit.top(limit=20)
                if not submission.stickied
            ]

        submission = submission_list[random.randint(0, len(submission_list) - 1)]

        return submission

    async def get_submission_from_url(self, reddit_url: str):
        submission = await self.reddit.submission(url=reddit_url)
        return submission

    async def get_redditor(self, redditor_name: str):
        redditor = await self.reddit.redditor(name=redditor_name, fetch=True)
        return redditor

    async def build_embed(self, ctx: commands.Context, submission: asyncpraw.models.Submission):
        """Embed that doesn't include a voting system."""

        VIDEO_URL = "v.redd.it"
        IMAGE_URL = "i.redd.it"

        downvotes = int(
            ((submission.score / (submission.upvote_ratio * 100)) * 100)
            - submission.score
        )

        if VIDEO_URL in submission.url:
            if hasattr(submission, "preview"):
                preview_image_link = submission.preview["images"][0]["source"]["url"]
                embed = Embed(
                    ctx,
                    title=submission.title,
                    thumbnail=preview_image_link,
                    url=submission.shortlink,
                )
            else:
                preview_image_link = "https://imgur.com/MKnguLq.png"
            embed = Embed(
                ctx,
                title=submission.title,
                thumbnail=preview_image_link,
                url=submission.shortlink,
            )
        elif IMAGE_URL in submission.url:
            embed = Embed(
                ctx,
                title=submission.title,
                image=submission.url,
                url=submission.shortlink,
            )
        else:
            embed = Embed(ctx, title=submission.title, url=submission.shortlink)
            embed.add_field(
                name="Text:",
                value=submission.selftext
                if len(submission.selftext) <= 1024
                else "This post is too long to fit in an Embed. Sending another massge with the text.",
                inline=False,
            )

        embed.add_fields(
            ("Post info:", f"<:upvote:754073992771666020> {submission.score} | <:downvote:754073959791722569> {downvotes} | :envelope: {submission.num_comments}"),
            (
                "Author:",
                f"[u/{submission.author.name}](https://reddit.com/u/{submission.author.name})",
            )
        )

        return embed


class Rule34API:
    def __init__(self, bot):
        self.rule34 = rule34.Rule34(loop=bot.loop)

    async def build_embed(self, ctx: commands.Context, file: rule34.Rule34Post):
        if any(x in file.file_url for x in VIDEO_FORMATS):
            embed = Embed(
                ctx,
                title="Video found",
                thumbnail=file.preview_url
            )
        else:
            embed = Embed(
                ctx,
                title="Image found.",
                image=file.file_url
            )

        if file.source:
            embed.add_field(
                name="Sauce from Rule34:", value=f"[Click Here!]({file.source})"
            )
        embed.add_field(name="File link:", value=f"[Click Here!]({file.file_url})")
        
        return embed

    async def get_random_r34(self, user_id: int, search: str):

        tags = Connect.get_field_value(db_name="users",document_id=user_id,field="r34_tags")
        tags += " " + search

        images = await self.rule34.getImages(tags=tags)
        try:
            file = images[random.randint(0, len(images))]
        except:
            raise exceptions.NoResultsFound

        return file


class BooruAPI:
    pass


class SauceNaoAPI:
    pass
