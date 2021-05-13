import discord
from discord.ext import commands
import datetime
from typing import Tuple
from . import static


class RoEmbed(discord.Embed):
    def __init__(self, ctx: commands.Context, title: str, colour=static.ColorEmbedDefault, **kwargs):
        super(RoEmbed, self).__init__(colour=colour, **kwargs)

        self.timestamp = ctx.message.created_at

        self.description = kwargs.get("description")

        self.set_footer(
            text=static.GitHubRepoShort,
            icon_url=static.GitHubIcon,
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
                url=static.GitHubRepo,
            )

    def add_fields(self, *fields: Tuple[str, str]):
        for name, value in fields:
            self.add_field(name=name, value=value, inline=True)


class ErrorEmbed(discord.Embed):
    def __init__(self, ctx: commands.Context, title: str, colour=static.ColorEmbedError, **kwargs):
        super(ErrorEmbed, self).__init__(colour=colour, **kwargs)

        self.timestamp = ctx.message.created_at

        self.description = kwargs.get("description")

        self.set_footer(
            text=static.GitHubRepoShort,
            icon_url=static.GitHubIcon,
        )

        self.set_author(
            name=title,
            icon_url=ctx.author.avatar_url,
            url=static.GitHubRepo,
        )