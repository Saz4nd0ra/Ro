from discord.ext import commands
from typing import Union
from .utils import context
from .utils.embed import Embed
import discord
import wavelink
import asyncio
import time
import itertools
from dotenv import load_dotenv
import os


class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()


class TrackDeque(asyncio.Queue):
    async def put_front(self, item):
        while self.full():
            putter = self._loop.create_future()
            self._putters.append(putter)
            try:
                await putter
            except:
                putter.cancel()  # Just in case putter is not done yet.
                try:
                    # Clean self._putters from canceled putters.
                    self._putters.remove(putter)
                except ValueError:
                    # The putter could be removed from self._putters by a
                    # previous get_nowait call.
                    pass
                if not self.full() and not putter.cancelled():
                    # We were woken up by get_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._putters)
                raise
        return self.put_front_nowait(item)

    def put_front_nowait(self, item):
        # if self.full():
        #   raise QueueFull
        self._put_front(item)
        self._unfinished_tasks += 1
        self._finished.clear()
        self._wakeup_next(self._getters)

    def _put_front(self, item):
        self._queue.appendleft(item)

    def clear(self):
        while not self.empty():
            self.get_nowait()
            self.task_done()


class MusicController:
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.channel = None

        self.next = asyncio.Event()
        self.queue = TrackDeque()

        self.volume = 40
        self.now_playing = None
        self.afk_timer = None

        self.bot.loop.create_task(self.controller_loop())

    async def controller_loop(self):
        await self.bot.wait_until_ready()

        player = self.bot.wavelink.get_player(self.guild_id)
        await player.set_volume(self.volume)

        while True:
            if self.now_playing:
                self.now_playing = None

            self.next.clear()

            self.afk_timer = Timer(300, self.afk_disconnect)  # 5 min timeout
            track = await self.queue.get()  # waits if queue empty
            self.afk_timer.cancel()

            await player.play(track)
            await self.bot.change_presence(
                activity=discord.Game(name=track.info["title"])
            )
            self.now_playing = track
            await self.channel.send(
                f"Now playing: **{self.now_playing}**", delete_after=10
            )

            await self.next.wait()

    async def afk_disconnect(self):
        player = self.bot.wavelink.get_player(self.guild_id)
        await player.stop()
        await player.disconnect()
        if self.channel:
            await self.channel.send(
                "Disconnected player due to inactivity...", delete_after=10
            )


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.controllers = {}
        if not hasattr(bot, "wavelink"):
            self.bot.wavelink = wavelink.Client(bot=self.bot)
        self.bot.loop.create_task(self.start_nodes())

    async def destroy_nodes(self):
        await self.node.destroy()

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        self.node = await self.bot.wavelink.initiate_node(
            host=self.config.ll_host,
            port=self.config.ll_port,
            rest_uri=f"http://{self.config.ll_host}:{self.config.ll_port}",
            password=self.config.ll_passwd,
            identifier="ADB",
            region="eu",
            heartbeat=45,  # heroku websocket timeout is 55 seconds
        )
        self.node.set_hook(self.on_event_hook)

    async def on_event_hook(self, event):
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackException)):
            controller = self.get_controller(event.player)
            await controller.bot.change_presence(activity=None)
            controller.next.set()

    def get_controller(self, value: Union[commands.Context, wavelink.Player]):
        if isinstance(value, commands.Context):
            guild_id = value.guild.id
        else:
            guild_id = value.guild_id

        try:
            controller = self.controllers[guild_id]
        except KeyError:
            controller = MusicController(self.bot, guild_id)
            self.controllers[guild_id] = controller

        return controller

    @commands.command()
    async def join(self, ctx, *, channel=None):
        """Invites bot to channel."""
        channel = getattr(ctx.author.voice, "channel", channel)
        if channel is None:
            return await ctx.error("No channel provided!")

        controller = self.get_controller(ctx)
        controller.channel = ctx.message.channel

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await ctx.embed(f"Connecting to **{channel.name}**")
        await player.connect(channel.id)

    @commands.command(aliases=["s", "disconnect"])
    async def stop(self, ctx):
        """Removes bot from channel."""
        player = self.bot.wavelink.get_player(ctx.guild.id)

        try:
            del self.controllers[ctx.guild.id]
        except KeyError:
            await player.stop()
            await player.disconnect()
            return await ctx.send("There's no controller to stop...", delete_after=10)

        await player.stop()
        await player.disconnect()
        await ctx.embed("Disconnected player and killed controller...", delete_after=10)

    @commands.command(aliases=["p", "play"])
    async def youtube(self, ctx, *, query):
        """Returns YouTube results by query."""
        search_query = f"ytsearch:{query}"

        tracks = await self.bot.wavelink.get_tracks(f"{search_query}")
        if not tracks:
            return await ctx.send("Couldn't find any songs with that query :(")

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await ctx.invoke(self.join)

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)

            await ctx.embed(
                f'`Added the playlist {tracks.data["playlistInfo"]["name"]}'
                f" with {len(tracks.tracks)} songs to the queue.\n`"
            )
        else:
            tracks = tracks[0:10 if 10 >= len(tracks) else len(tracks) - 1]
            query_result = ""
            for i, track in enumerate(tracks):
                s = track.info["length"] / 1000
                query_result += f'**{i+1})** {track.info["title"]} - {time.strftime("%H:%M:%S", time.gmtime(s))}\n{track.info["uri"]}\n'
            query_embed = discord.Embed(description=query_result)
            await ctx.channel.send(embed=query_embed)

        response = await self.bot.wait_for(
            "message", check=lambda m: m.author.id == ctx.author.id, timeout=30
        )
        if 1 <= int(response.content) <= 10:
            track = tracks[int(response.content) - 1]

            controller = self.get_controller(ctx)
            controller.channel = ctx.message.channel
            await controller.queue.put(track)
            await ctx.send(f"Added to the queue: **{str(track)}**")

    @commands.command(aliases=["sc"])
    async def soundcloud(self, ctx, *, query):
        """Plays a song from SoundCloud."""
        search_query = f"scsearch:{query}"

        tracks = await self.bot.wavelink.get_tracks(f"{search_query}")
        if not tracks:
            return await ctx.send("Couldn't find any songs with that query :(")

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await ctx.invoke(self.join)

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)

            await ctx.embed(
                f'`Added the playlist {tracks.data["playlistInfo"]["name"]}'
                f" with {len(tracks.tracks)} songs to the queue.\n`"
            )
        else:
            tracks = tracks[0:10 if 10 >= len(tracks) else len(tracks) - 1]
            query_result = ""
            for i, track in enumerate(tracks):
                s = track.info["length"] / 1000
                query_result += f'**{i+1})** {track.info["title"]} - {time.strftime("%H:%M:%S", time.gmtime(s))}\n{track.info["uri"]}\n'
            query_embed = discord.Embed(description=query_result)
            await ctx.channel.send(embed=query_embed)

        response = await self.bot.wait_for(
            "message", check=lambda m: m.author.id == ctx.author.id, timeout=30
        )
        if 1 <= int(response.content) <= 10:
            track = tracks[int(response.content) - 1]

            controller = self.get_controller(ctx)
            controller.channel = ctx.message.channel
            await controller.queue.put(track)
            await ctx.send(f"Added to the queue: **{str(track)}**")

    @commands.command()
    async def pause(self, ctx):
        """Pauses currently playing song."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("I'm not playing anything!", delete_after=10)

        await ctx.send("Pausing the song!", delete_after=10)
        await player.set_pause(True)

    @commands.command()
    async def resume(self, ctx):
        """Resumes currently paused song."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.paused:
            return await ctx.send("I'm not currently paused!", delete_after=10)

        await ctx.send("Resuming the song!", delete_after=10)
        await player.set_pause(False)

    @commands.command()
    async def skip(self, ctx):
        """Skips currently playing song."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("I'm not playing anything!", delete_after=10)

        await ctx.send("Skipping the song!", delete_after=10)
        await player.stop()

    @commands.command()
    async def volume(self, ctx, *, vol: int):
        """Adjust music volume."""

        if not 0 < vol < 101:
            return await ctx.error("Please enter a value between 1 and 100.")

        player = self.bot.wavelink.get_player(ctx.guild.id)
        controller = self.get_controller(ctx)
        controller.volume = vol

        await ctx.send(f"Setting player volume to {controller.volume}", delete_after=10)
        await player.set_volume(controller.volume)

    @commands.command(aliases=["nowplaying", "np"])
    async def now_playing(self, ctx):
        """Returns currently playing song."""
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.current:
            return await ctx.send("I'm not playing anything!", delete_after=10)

        # controller = self.get_controller(ctx)
        # await controller.now_playing.delete()
        # controller.now_playing = player.current

        await ctx.send(f"Now playing: **{player.current}**")

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        """Returns song queue info."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        controller = self.get_controller(ctx)

        if not player.current or not controller.queue._queue:
            return await ctx.send(
                "There are no songs currently in the queue.", delete_after=10
            )

        upcoming = list(itertools.islice(controller.queue._queue, 0, 5))

        fmt = "\n".join(f"**`{str(track)}`**" for track in upcoming)
        embed = discord.Embed(title=f"Upcoming - Next {len(upcoming)}", description=fmt)

        await ctx.send(
            f"Total number of songs in queue: {len(controller.queue._queue)}"
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["c"])
    async def clear(self, ctx):
        """Empties the song queue."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        controller = self.get_controller(ctx)

        if not player.current or not controller.queue._queue:
            return await ctx.send(
                "There are no songs currently in the queue.", delete_after=10
            )

        controller.queue.clear()
        await ctx.send("Emptied the song queue.", delete_after=10)

    @commands.command(aliases=["m"])
    async def move(self, ctx, entry: int, new_position: int):
        """Move a queue entry to a new position."""

        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if player.queue.qsize() == 0:
            return await ctx.error("There are no songs in the queue...")

        if not player.queue._queue[entry - 1]:
            return await ctx.error("This entry doesn't exists...")

        tmp = player.queue._queue[new_position - 1]

        player.queue._queue[new_position - 1] = player.queue._queue[entry - 1]

        player.queue._queue[entry - 1] = tmp

        await ctx.embed("Song successfully moved.")

def setup(bot):
    bot.add_cog(Music(bot))
