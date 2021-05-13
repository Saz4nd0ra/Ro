import discord
from discord.utils import get
import wavelink
from discord.ext import commands
import asyncio
import datetime as dt
import random
import re
import spotipy
from enum import Enum
from spotipy.oauth2 import SpotifyClientCredentials
from .utils.embed import RoEmbed
from .utils.context import Context
from .utils.config import Config
from .utils import exceptions
from .utils.exceptions import *

SPOTIFY_URL_REGEX = r"[\bhttps://open.\b]*spotify[\b.com\b]*[/:]*[/:]*[A-Za-z0-9?=]+"
YOUTUBE_URL_REGEX = (
    r"(?:https?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/"
    r"(?:watch|v|embed)(?:\.php)?(?:\?.*v=|\/))([a-zA-Z0-9\_-]+)"
)

OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}


class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2


class Spotify:
    def __init__(self):
        self.config = Config()
        self.credentials_manager = SpotifyClientCredentials(
            self.config.spotify_client_id, self.config.spotify_client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=self.credentials_manager)

    async def get_track(self, url: str):
        """Gets a single track from Spotify."""
        track = self.sp.track(url)
        return track["name"] + track["artists"][0]["name"]

    async def get_playlist_tracks(self, url: str):
        """Gets a playlist from Spotify."""
        results = self.sp.playlist_tracks(url)

        tracks_list = list()

        for i in range(0, len(results["items"])):
            tracks_list.append(
                results["items"][i]["track"]["name"]
                + " "
                + results["items"][i]["track"]["artists"][0]["name"]
            )

        return tracks_list

    async def get_album_tracks(self, url: str):
        """Gets an album from Spotify."""
        results = self.sp.album_tracks(url)

        tracks_list = list()

        for i in range(0, len(results["items"])):
            tracks_list.append(
                results["items"][i]["name"]
                + " "
                + results["items"][i]["artists"][0]["name"]
            )

        return tracks_list


class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = "requester"

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get("requester")


class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if not self._queue:
            raise exceptions.QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise exceptions.QueueIsEmpty

        return self._queue[self.position + 1 :]

    @property
    def history(self):
        if not self._queue:
            raise exceptions.QueueIsEmpty

        return self._queue[: self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get_next_track(self):
        if not self._queue:
            raise exceptions.QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None

        return self._queue[self.position]

    def shuffle(self):
        if not self._queue:
            raise exceptions.QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[: self.position + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "1":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "all":
            self.repeat_mode = RepeatMode.ALL

    def empty(self):
        self._queue.clear()
        self.position = 0


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

        self.context = kwargs.get("context", None)
        if self.context:
            self.dj = self.context.author

    async def connect(self, ctx: commands.Context, channel=None):
        if self.is_connected:
            raise exceptions.AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise exceptions.NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx: commands.Context, tracks: list):
        if not tracks:
            raise exceptions.NoTracksFound

        if isinstance(tracks, wavelink.TrackPlaylist):
            queue = []
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                queue.append(track)
                self.queue.add(track)
            embed = RoEmbed(
                ctx,
                title="Playlist added to queue",
                description=f"Added {len(queue)} tracks to the queue.",
                thumbnail=queue[0].thumb,
            )
            await ctx.send(embed=embed)

        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            self.queue.add(track)
            if self.queue.length == 0:
                embed = RoEmbed(
                    ctx,
                    title="Song added to queue",
                    description=f"Now playing [{track.title}]({track.uri})",
                    thumbnail=track.thumb,
                )
                await ctx.send(embed=embed)
            else:
                embed = RoEmbed(
                    ctx,
                    title="Song added to queue",
                    description=f"Added [{track.title}]({track.uri}) to the queue.",
                    thumbnail=track.thumb,
                )
                await ctx.send(embed=embed)

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def search_tracks(self, ctx: commands.Context, tracks: list):
        embed = RoEmbed(
            ctx,
            title=f"Search for music",
            description=(
                "\n".join(
                    f"[{t.title}](https://www.youtube.com/watch?v={t.ytid}) "
                    f"({t.length // 60000}:{str(t.length % 60).zfill(2)})"
                    for t in tracks[:15]
                )
            ),
            thumbnail=tracks[0].thumb,
        )

        await ctx.send(embed=embed)

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except exceptions.QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)


class Music(commands.Cog, wavelink.WavelinkMixin):
    """The obligatory Music Cog."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.spotify = Spotify()
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.ONE:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.error("Music commands are not available in DMs!")
            return False

        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        nodes = {
            "MAIN": {
                "host": f"{self.config.ll_host}",
                "port": f"{self.config.ll_port}",
                "rest_uri": f"http://{self.config.ll_host}:{self.config.ll_port}",
                "password": f"{self.config.ll_passwd}",
                "identifier": "MAIN",
                "region": "eu",
            }
        }

        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    async def add_spotify_tracks(self, ctx: commands.Context, spotify_tracks: list):
        player = self.get_player(ctx)
        queue = []
        await ctx.embed(
            "Processing spotify playlist/album... this could take some time..."
        )
        playlist_length = len(spotify_tracks)
        for i in range(0, len(spotify_tracks)):
            query = f"ytsearch:{spotify_tracks[i]}"
            track = await self.wavelink.get_tracks(query)
            try:
                track = Track(track[0].id, track[0].info, requester=ctx.author)
                queue.append(track)
                player.queue.add(track)
            except:
                playlist_length - 1
                continue

        embed = RoEmbed(
            ctx,
            title="Playlist added to queue",
            description=f"Added {playlist_length} tracks to the queue.",
            thumbnail=queue[0].thumb,
        )
        await ctx.send(embed=embed)

        if not player.is_playing and not player.queue.is_empty:
            await player.start_playback()

    @commands.command(name="connect", aliases=["join"])
    async def connect_command(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        """Connect the player to a channel of your choice."""
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.embed(f"Connected to {channel.name}.")

    @connect_command.error
    async def connect_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.AlreadyConnectedToChannel):
            await ctx.error("Already connected to a voice channel.")
        elif isinstance(exc, exceptions.NoVoiceChannel):
            await ctx.error("No suitable voice channel was provided.")

    @commands.command(name="disconnect", aliases=["leave"])
    async def disconnect_command(self, ctx: commands.Context):
        """Disconnect the player."""
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.embed("Disconnected.")

    @commands.command(name="play", aliases=["p"])
    async def play_command(self, ctx: commands.Context, *, query: str):
        """Play a song or playlist. Either enter a search term or a link to the song or playlist."""
        player = self.get_player(ctx)

        if not player.is_connected:
            await player.connect(ctx)

        if re.search(SPOTIFY_URL_REGEX, query):
            if "/track/" in query:
                track = await self.spotify.get_track(query)
                query = f"ytsearch:{track}"
                await player.add_tracks(ctx, await self.wavelink.get_tracks(query))
            elif "/playlist/" in query:
                spotify_tracks = await self.spotify.get_playlist_tracks(query)
                await self.add_spotify_tracks(ctx, spotify_tracks)
            elif "/album/" in query:
                spotify_tracks = await self.spotify.get_album_tracks(query)
                await self.add_spotify_tracks(ctx, spotify_tracks)
            else:
                raise exceptions.ProbablyInvalidSpotifyLink
        elif re.search(YOUTUBE_URL_REGEX, query):
            query = query.strip("<>")
            query = f"ytsearch:{query}"
            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))
        else:
            query = f"ytsearch:{query}"
            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))



    @play_command.error
    async def play_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.QueryError):
            await ctx.error("There was an error with your query")
        elif isinstance(exc, exceptions.NoVoiceChannel):
            await ctx.error("No suitable voice channel was provided.")
        elif isinstance(exc, exceptions.ProbablyInvalidSpotifyLink):
            await ctx.error(
                "The spotify link doesn't link to a track, playlist or album apparently."
            )

    @commands.command(name="search")
    async def search(self, ctx: commands.Context, *, query: str):
        """Search for a song on Youtube or SoundCloud."""
        player = self.get_player(ctx)
        query = query.strip("<>")
        if not re.match(YOUTUBE_URL_REGEX, query):
            query = f"ytsearch:{query}"

        await player.search_tracks(ctx, await self.wavelink.get_tracks(query))

    @commands.command(name="pause")
    async def pause_command(self, ctx):
        """Pause the playback."""
        player = self.get_player(ctx)

        if player.is_paused:
            raise exceptions.PlayerIsAlreadyPaused

        await player.set_pause(True)
        await ctx.embed("Playback paused.")

    @pause_command.error
    async def pause_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.PlayerIsAlreadyPaused):
            await ctx.error("Already paused.")

    @commands.command(name="resume")
    async def resume_command(self, ctx: commands.Context):
        """Resume the playback."""
        player = self.get_player(ctx)

        if not player.is_paused:
            raise exceptions.PlayerIsNotPaused

        await player.set_pause(False)
        await ctx.embed("Playback resumed.")

    @resume_command.error
    async def resume_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.PlayerIsNotPaused):
            await ctx.error("Player is not paused.")

    @commands.command(name="stop")
    async def stop_command(self, ctx: commands.Context):
        """Stop the playback and yeet the player."""
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.embed("Playback stopped.")

    @commands.command(name="next", aliases=["skip", "s"])
    async def next_command(self, ctx: commands.Context):
        """Play the next song, aka skip."""
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            raise exceptions.NoMoreTracks

        await player.stop()
        await ctx.embed("Playing next track in queue.")

    @next_command.error
    async def next_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.QueueIsEmpty):
            await ctx.error("The queue is non-existent.")

        elif isinstance(exc, exceptions.NoMoreTracks):
            await ctx.error("There are no more tracks in the queue.")

    @commands.command(name="previous")
    async def previous_command(self, ctx: commands.Context):
        """Play the previous song."""
        player = self.get_player(ctx)

        if not player.queue.history:
            raise exceptions.NoPreviousTracks

        player.queue.position -= 2
        await player.stop()
        await ctx.send("Playing previous track in queue.")

    @previous_command.error
    async def previous_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.QueueIsEmpty):
            await ctx.error("The queue is empty.")
        elif isinstance(exc, exceptions.NoPreviousTracks):
            await ctx.error("There are no previous tracks in the queue.")

    @commands.command(name="shuffle")
    async def shuffle_command(self, ctx: commands.Context):
        """Shuffle the queue."""
        player = self.get_player(ctx)
        player.queue.shuffle()
        await ctx.embed("Queue shuffled.")

    @shuffle_command.error
    async def shuffle_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.QueueIsEmpty):
            await ctx.error("You can't shuffle an empty queue.")

    @commands.command(name="repeat")
    async def repeat_command(self, ctx: commands.Context, mode: str):
        """Repeat the current song once, or loop it forever."""
        if mode not in ("none", "1", "all"):
            raise exceptions.InvalidRepeatMode

        player = self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        await ctx.embed(f"The repeat mode has been set to {mode}.")

    @repeat_command.error
    async def repeat_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.InvalidRepeatMode):
            await ctx.error("Invalid repeat mode given.")

    @commands.command(name="queue", aliases=["q"])
    async def queue_command(self, ctx: commands.Context):
        """Show the current queue."""
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise exceptions.QueueIsEmpty

        final_string = ""
        titles = [track.title for track in player.queue.upcoming[:10]]
        uris = [track.uri for track in player.queue.upcoming[:10]]
        requester = [track.requester for track in player.queue.upcoming[:10]]

        queue_length_time = 0

        for track in player.queue.upcoming:
            queue_length_time += track.length

        if len(titles) >= 10:
            upper_limit = 10
        else:
            upper_limit = len(titles)

        for i in range(0, upper_limit):
            final_string += (
                f"{i + 1}. [{titles[i]}]({uris[i]}) | Requested by: {requester[i]}\n\n"
            )

        embed = RoEmbed(
            ctx,
            title=f"Queue for {ctx.channel.name}",
            description="**Now Playing:**\n\n"
            f"[{player.queue.current_track.title}]({player.queue.current_track.uri}) | Requested by: {player.queue.current_track.requester}\n\n"
            "**Up next:\n\n**"
            f"{final_string}"
            f"**{len(player.queue.upcoming)} songs in queue**",
        )

        await ctx.send(embed=embed)

    @queue_command.error
    async def queue_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.QueueIsEmpty):
            await ctx.error("The queue is empty.")

    @commands.command(name="move", aliases=["m"])
    async def move_command(self, ctx: commands.Context, entry: int, new_position: int):
        """Move a queue entry to a new position."""

        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if player.queue.is_empty:
            raise exceptions.QueueIsEmpty

        if not player.queue._queue[entry - 1]:
            raise exceptions.InvalidQueueEntry

        if not player.queue._queue[new_position - 1]:
            raise exceptions.InvalidQueuePosition

        tmp = player.queue._queue[new_position - 1]

        player.queue._queue[new_position - 1] = player.queue._queue[entry - 1]

        player.queue._queue[entry - 1] = tmp

        await ctx.embed("Song successfully moved.")

    @move_command.error
    async def move_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.QueueIsEmpty):
            await ctx.error("The queue is empty.")
        if isinstance(exc, exceptions.InvalidQueueEntry):
            await ctx.error("This entry doesn't exist.")
        if isinstance(exc, exceptions.InvalidQueuePosition):
            await ctx.error("This position is invalid.")

    @commands.command(name="clear")
    async def clear_command(self, ctx: commands.Context):
        """Clear the queue."""

        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise exceptions.QueueIsEmpty

        player.queue.empty()

        await ctx.embed("Queue successfully cleared.")

    @clear_command.error
    async def clear_command_error(self, ctx: commands.Context, exc):
        if isinstance(exc, exceptions.QueueIsEmpty):
            await ctx.error("The queue is empty.")


def setup(bot):
    bot.add_cog(Music(bot))
