import asyncpraw
from .config import Config
import random
import asyncio
from .embed import Embed


VIDEO_FORMATS = [
    "mp4",
    "webm",
    # and so on, I don't really know which formats r34 uses
]

def send_embed(ctx, obj):
    pass


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
            submission_list = [submission async for submission in subreddit.hot(limit=20) if not submission.stickied]
        elif sorting == "new":
            submission_list = [submission async for submission in subreddit.new(limit=20) if not submission.stickied]
        else:
            submission_list = [submission async for submission in subreddit.top(limit=20) if not submission.stickied]

        submission = submission_list[random.randint(0, len(submission_list) - 1)]

        return submission

    async def get_submission_from_url(self, reddit_url: str):
        submission = await self.reddit.submission(url=reddit_url)
        return submission

    async def get_redditor(self, redditor_name: str):
        redditor = await self.reddit.redditor(name=redditor_name, fetch=True)
        return redditor

    async def build_embed(self, ctx, submission: asyncpraw.models.Submission = None):
        """Embed that doesn't include a voting system."""

        VIDEO_URL = "v.redd.it"
        IMAGE_URL = "i.redd.it"
        
        downvotes = int(
            ((submission.score / (submission.upvote_ratio * 100)) * 100) - submission.score
        )

        if VIDEO_URL in submission.url:
            if hasattr(submission, "preview"):
                preview_image_link = submission.preview["images"][0]["source"]["url"]
                embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link, url=submission.shortlink)
            else:
                preview_image_link = "https://imgur.com/MKnguLq.png"
            embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link, url=submission.shortlink)
        elif IMAGE_URL in submission.url:
            embed = Embed(ctx, title=submission.title, image=submission.url, url=submission.shortlink)
        else:
            embed = Embed(ctx, title=submission.title, url=submission.shortlink)
            embed.add_field(
                name="Text:",
                value=submission.selftext
                if len(submission.selftext) <= 1024
                else "This post is too long to fit in an Embed. Sending another massge with the text.",
                inline=False
            )

        embed.add_fields(
            ("Upvotes:", f"{submission.score}"),
            ("Downvotes:", f"{downvotes}"),
            ("Comments:", f"{submission.num_comments}"),
            ("Author:",f"[u/{submission.author.name}](https://reddit.com/u/{submission.author.name})"),
            ("Subreddit:", f"[r/{submission.subreddit}](https://reddid.com/r/{submission.subreddit})"),
            ("Link:", f"{submission.shortlink}"))

        return embed


class Rule34API:
    pass

class BooruAPI:
    pass

class SauceNaoAPI:
    pass
