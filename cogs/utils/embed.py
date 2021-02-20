import discord
import datetime
from typing import Tuple


class Embed(discord.Embed):
    def __init__(self, ctx, title, colour=0x7289DA, **kwargs):
        super(Embed, self).__init__(colour=colour, **kwargs)

        self.timestamp = ctx.message.created_at

        self.description = kwargs.get("description")

        self.set_footer(
            text="Saz4nd0ra/another-discord-bot",
            icon_url="https://cdn3.iconfinder.com/data/icons/popular-services-brands/512/github-512.png",
        )

        if kwargs.get("image"):
            self.set_image(url=kwargs.get("image"))

        if kwargs.get("thumbnail"):
            self.set_thumbnail(url=kwargs.get("thumbnail"))

        if kwargs.get("url"):
            self.set_author(
                name=title, icon_url=ctx.author.avatar_url, url=kwargs.get("url")
            )
        else:
            self.set_author(
                name=title,
                icon_url=ctx.author.avatar_url,
                url="https://github.com/Saz4nd0ra/another-discord-bot",
            )

    def add_fields(self, *fields: Tuple[str, str]):
        for name, value in fields:
            self.add_field(name=name, value=value, inline=True)

    @classmethod
    def error(cls, colour=0xF5291B, **kwargs):
        return cls(colour=colour, **kwargs)

    @classmethod
    def warning(cls, colour=0xF55C1B, **kwargs):
        return cls(colour=colour, **kwargs)


