import asyncpraw
from .config import Config
import random
from rule34 import Rule34
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

    async def get_submission(self, subreddit: str, sorting: str):
        if sorting == "hot":
            submissions = await self.reddit.subreddit(subreddit).hot(limit=100)
        elif sorting == "new":
            submissions = await self.reddit.subreddit(subreddit).new(limit=3)
        else:
            submissions = await self.reddit.subreddit(subreddit).top(limit=100)

        post_to_pick = random.randint(1, 100)

        for x in range(0, post_to_pick):
            submission = next(x for x in submissions if not x.stickied)
        return submission

    async def get_submission_from_url(self, url: str):
        submission = await self.reddit.submission(url)
        return submission

    async def get_user(self, name: str):
        user = await self.reddit.redditor(name)
        return user

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
                embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link)
            else:
                preview_image_link = "https://imgur.com/MKnguLq.png"
            embed = Embed(ctx, title=submission.title, thumbnail=preview_image_link)
        elif IMAGE_URL in submission.url:
            embed = Embed(ctx, title=submission.title, image=submission.url)
        else:
            embed = Embed(ctx, title=submission.title)
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
            ("Link:", f"{submission.shortlink}"))

        return embed


class Rule34API:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.rule34 = Rule34(self.loop)

    async def search_r34(self, search):
        pass

class BooruAPI:
    pass

class SauceNaoAPI:
    pass
