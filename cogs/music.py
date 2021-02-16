import discord
from discord.utils import get
import wavelink
from discord.ext import commands
import asyncio
import datetime as dt
import random
import re
from enum import Enum
from .utils.embed import Embed
from .utils.context import Context
from .utils.config import Config


URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}


class AlreadyConnectedToChannel(commands.CommandError):
    pass

class NoVoiceChannel(commands.CommandError):
    pass

class QueueIsEmpty(commands.CommandError):
    pass

class NoTracksFound(commands.CommandError):
    pass

class PlayerIsAlreadyPaused(commands.CommandError):
    pass

class PlayerIsNotPaused(commands.CommandError):
    pass

class NoMoreTracks(commands.CommandError):
    pass

class NoPreviousTracks(commands.CommandError):
    pass

class InvalidRepeatMode(commands.CommandError):
    pass

class InvalidQueueEntry(commands.CommandError):
    pass

class InvalidQueuePosition(commands.CommandError):
    pass

class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2


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
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

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
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
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

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                self.queue.add(track)
            await ctx.embed(
                f"Added the playlist {tracks.data['playlistInfo']['name']}"
                f"with {len(tracks.tracks)} songs to the queue.\n"
            )
        elif len(tracks) == 1:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            self.queue.add(track)
            await ctx.embed(f"Added {track.title} to the queue.")
        else:
            if (chosen_track := await self.choose_track(ctx, tracks)) is not None:
                track = Track(chosen_track.id, chosen_track.info, requester=ctx.author)
                self.queue.add(track)
                await ctx.embed(f"Added {track.title} to the queue.")

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == msg.id
            )

        embed = Embed(
            ctx,
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** {t.title} ({t.length//60000}:{str(t.length%60).zfill(2)})"
                    for i, t in enumerate(tracks[:5])
                )
            )
        )

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)


class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f" Wavelink node `{node.identifier}` ready.")

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

    @commands.command(name="connect", aliases=["join"])
    async def connect_command(self, ctx, *, channel: discord.VoiceChannel):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.embed(f"Connected to {channel.name}.")

    @connect_command.error
    async def connect_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            await ctx.error("Already connected to a voice channel.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.error("No suitable voice channel was provided.")

    @commands.command(name="disconnect", aliases=["leave"])
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.embed("Disconnected.")

    @commands.command(name="play", aliases=["p"])
    async def play_command(self, ctx, *, query: str):
        player = self.get_player(ctx)

        if not player.is_connected:
            await player.connect(ctx)

        
        query = query.strip("<>")
        if not re.match(URL_REGEX, query):
            query = f"ytsearch:{query}"

        await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @play_command.error
    async def play_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.error("The queue is empty.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.error("No suitable voice channel was provided.")

    @commands.command(name="pause")
    async def pause_command(self, ctx):
        """Pause the playback."""
        player = self.get_player(ctx)

        if player.is_paused:
            raise PlayerIsAlreadyPaused

        await player.set_pause(True)
        await ctx.embed("Playback paused.")

    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.error("Already paused.")

    @commands.command(name="resume")
    async def resume_command(self, ctx):
        """Resume the playback."""
        player = self.get_player(ctx)

        if not player.is_paused:
            raise PlayerIsNotPaused

        await player.set_pause(False)
        await ctx.embed("Playback resumed.")

    @resume_command.error
    async def resume_command_error(self, ctx, exc):
        if isinstance(exc, PlayIsNotPaused):
            await ctx.error("Player is not paused.")

    @commands.command(name="stop")
    async def stop_command(self, ctx):
        """Stop the playback and yeet the player."""
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.embed("Playback stopped.")

    @commands.command(name="next", aliases=["skip", "s"])
    async def next_command(self, ctx):
        """Play the next song, aka skip."""
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            raise NoMoreTracks

        await player.stop()
        await ctx.embed("Playing next track in queue.")

    @next_command.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.error("The queue is non-existent.")

        elif isinstance(exc, NoMoreTracks):
            await ctx.error("There are no more tracks in the queue.")

    @commands.command(name="previous")
    async def previous_command(self, ctx):
        """Play the previous song."""
        player = self.get_player(ctx)

        if not player.queue.history:
            raise NoPreviousTracks

        player.queue.position -= 2
        await player.stop()
        await ctx.send("Playing previous track in queue.")

    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.error("The queue is empty.")
        elif isinstance(exc, NoPreviousTracks):
            await ctx.error("There are no previous tracks in the queue.")


    @commands.command(name="shuffle")
    async def shuffle_command(self, ctx):
        """Shuffle the queue."""
        player = self.get_player(ctx)
        player.queue.shuffle()
        await ctx.embed("Queue shuffled.")

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.error("You can't shuffle an empty queue.")

    @commands.command(name="repeat")
    async def repeat_command(self, ctx, mode: str):
        """Repeat the current song once, or loop it forever."""
        if mode not in ("none", "1", "all"):
            raise InvalidRepeatMode

        player = self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        await ctx.embed(f"The repeat mode has been set to {mode}.")

    @commands.command(name="queue", aliases=["q"])
    async def queue_command(self, ctx):
        """Show the current queue."""
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        final_string = []
        titles = [track.title for track in player.queue.upcoming[:10]]
        uris = [track.uri for track in player.queue.upcoming[:10]]
        requester = [track.requester.name for track in player.queue.upcoming[:10]]

        if len(titles) <= 10:
            upper_limit = len(titles)
        else:
            upper_limit = 10

        for i in range(0, upper_limit):
            final_string.append(f"{i + 1}. [{titles[i]}]({uris[i]}) | Requested by: {requester[i]}\n")

        embed = Embed(
            ctx,
            title=f"Queue for {ctx.channel.name}",
            description=f"Showing the next 10 tracks. | Total queue length: {len(player.queue.upcoming)}"
        )
        embed.add_field (name="Now Playing:\n", value=f"[{player.queue.current_track.title}]({player.queue.current_track.uri}) | Requested by: {player.queue.current_track.requester.name}\n", inline=False)
        if upcoming := player.queue.upcoming:
            embed.add_field(name="Up next:\n", value="\n".join(
            f"{string}" for string in final_string), inline=False)

        await ctx.send(embed=embed)

    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.error("The queue is empty.")


    @commands.command(name="move", aliases=["m"])
    async def move_command(self, ctx, entry: int, new_position: int):
        """Move a queue entry to a new position."""

        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not player.queue._queue[entry - 1]:
            raise InvalidQueueEntry

        if not player.queue._queue[new_position -1]:
            raise InvalidQueuePosition

        tmp = player.queue._queue[new_position - 1]

        player.queue._queue[new_position - 1] = player.queue._queue[entry - 1]

        player.queue._queue[entry - 1] = tmp

        await ctx.embed("Song successfully moved.")

    @move_command.error
    async def move_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.error("The queue is empty.")
        if isinstance(exc, InvalidQueueEntry):
            await ctx.error("This entry doesn't exist.")
        if isinstance(exc, InvalidQueuePosition):
            await ctx.error("This position is invalid.")
        

def setup(bot):
    bot.add_cog(Music(bot))
