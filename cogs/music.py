import math
from contextlib import suppress
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import pomice

class Player(pomice.Player):
    """Custom music cog."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = pomice.Queue()
        self.controller: discord.Message = None
        self.context: commands.Context = None
        self.dj: discord.Member = None

        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()

    async def do_next(self) -> None:
        player: Player = self.context.voice_client
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        if self.controller:
            with suppress(discord.HTTPException):
                await self.controller.delete()
        try:
            track: pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            return await self.teardown()

        await self.play(track)

        if track.is_stream:
            embed = discord.Embed(
                title="Live",
                description=f"[{track.title}]({track.uri}) [By {track.requester.mention}]",
                color=0x00ffff,
            )
            self.controller = await self.context.send(embed=embed)
        else:
            if player.is_paused:
                embed = discord.Embed(
                    title=f"Now playing (Paused)",
                    description=f"[{track.title}]({track.uri}) [{track.requester.mention}]",
                    color=0x00ffff,
                )
            if not player.is_paused:
                embed = discord.Embed(
                    title=f"Playing",
                    description=f"[{track.title}]({track.uri}) [{track.requester.mention}]",
                    color=0x00ffff,
                )
            view = MyView()
            buton_stop = discord.ui.Button(label="⏹| Stop", style=discord.ButtonStyle.red)
            buton_skip = discord.ui.Button(label="⏭| Skip", style=discord.ButtonStyle.primary)
            buton_pause = discord.ui.Button(label="⏸| Pause", style=discord.ButtonStyle.primary)
            buton_queue = discord.ui.Button(label="📃| Queue", style=discord.ButtonStyle.primary)

            async def buttonqueue_callback(interaction):
                if not self.context.author.voice:
                    await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True)
                else:
                    queue_list = []
                    for index, track in enumerate(player.queue._queue, start=1):
                        queue_list.append(f"{index}. **{track.title}** [Added by {track.requester.mention}]")

                    queue_message = "\n".join(queue_list)
                    embed = discord.Embed(title="Current Playlist", description=queue_message, color=0x00ffff)
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            async def buttonpause_callback(interaction):
                if not self.context.author.voice:
                    await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True)
                else:
                    if player.is_paused: 
                        em = discord.Embed(description=f"{interaction.user.mention} has resumed the player.", color=0x00ffff)
                        await interaction.response.send_message(embed=em, ephemeral=True)
                        await player.set_pause(False)
                        embed.title = f"Playing"
                        buton_pause.label="⏸| Pause"
                        buton_pause.style=discord.ButtonStyle.primary
                        await self.controller.edit(embed=embed, view=view)
                    if not player.is_paused:   
                        em = discord.Embed(description=f"{interaction.user.mention} has paused the player.", color=0x00ffff)
                        await interaction.response.send_message(embed=em, ephemeral=True)
                        await player.set_pause(True)
                        buton_pause.label="▶| Resume"
                        buton_pause.style=discord.ButtonStyle.green
                        embed.title = f"Paused by {interaction.user.name} "
                        await self.controller.edit(embed=embed, view=view)

            async def buttonskip_callback(interaction):
                if not self.context.author.voice:
                    await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True)
                else:
                    embed = discord.Embed(description=f"{interaction.user.mention} has skipped the song.", color=0x00ffff)
                    await interaction.response.send_message(embed=embed, delete_after=15)
                    await player.stop()
            
            async def buttonstop_callback(interaction):
                if not self.context.author.voice:
                    await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True)
                else:
                    embed = discord.Embed(description=f"{interaction.user.mention} has stopped the player.", color=0x00ffff)
                    await interaction.response.send_message(embed=embed, delete_after=15)
                    await self.teardown()
            
            buton_stop.callback = buttonstop_callback
            buton_skip.callback = buttonskip_callback
            buton_pause.callback = buttonpause_callback
            buton_queue.callback = buttonqueue_callback
            view.add_item(buton_stop)
            view.add_item(buton_skip)
            view.add_item(buton_pause)
            view.add_item(buton_queue)
            self.controller = await self.context.send(embed=embed, view=view)

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""
        with suppress((discord.HTTPException), (KeyError)):
            await self.destroy()
            if self.controller:
                await self.controller.delete()

    async def set_context(self, ctx: commands.Context):
        """Set context for the player"""
        self.context = ctx
        self.dj = ctx.author


class MyView(discord.ui.View):
    def __init__(self):
        super().__init__()
    

    ###idee dar nu merge????
    ###@discord.ui.button(emoji="🛑", label="| Stop", style=discord.ButtonStyle.red)
    ###async def stop_button(self, interaction, button):
    ###    await interaction.response.send_message(content="Stopped the player. (in test, not working)", view=self, ephemeral=True, delete_after=5)

    ###@discord.ui.button(emoji="⏭", label="| Skip", style=discord.ButtonStyle.primary)
    ###async def skip_button(self, interaction, button):
    ###    await interaction.response.send_message(content="Skipped the song. (in test, not working)", view=self, ephemeral=True, delete_after=5)

class Music(commands.GroupCog, name="music", description="Music commands."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # cream nodul
        self.pomice = pomice.NodePool()
        # pornim nodul
        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        # se conecteaza la nod
        await self.pomice.create_node(
            bot=self.bot,
            host="0.0.0.0",
            port=2333,
            password="passwd",
            identifier="MAIN",
        )
        print(f"[NOD] Connected to the server.")

    def required(self, ctx: commands.Context):
        """Calculate the required votes to pass a vote."""
        player: Player = ctx.voice_client
        channel = self.bot.get_channel(int(player.channel.id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == "stop":
            if len(channel.members) == 3:
                required = 2

        return required

    def is_privileged(self, ctx: commands.Context):
        """Check whether the user is an Admin or DJ."""
        player: Player = ctx.voice_client

        return player.dj == ctx.author or ctx.author.guild_permissions.move_members or ctx.author.guild_permissions.mute_members

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: Player, track, _):
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: Player, track, _):
        await player.do_next()

    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: Player, track, _):
        await player.do_next()


    @commands.hybrid_command(aliases=["joi", "j", "summon", "su", "con", "connect"], description="Potato will connect to the voice channel you are in.")
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None) -> None:
        """Potato will join."""
        
        channel = ctx.author.voice.channel
        if not channel.permissions_for(ctx.me).connect:
            return await ctx.send("I don't have permission to connect to the voice channel.", ephemeral=True)

        if not channel:
            channel = getattr(ctx.author.voice, "channel", None)
            if not channel:
                return await ctx.send("You must be in a voice channel in order to use this command.", ephemeral=True)
        
        await ctx.author.voice.channel.connect(cls=Player)
        player: Player = ctx.voice_client
        await player.set_context(ctx=ctx)
        await ctx.send(f"Joined the voice channel `{channel.name}`")

    @commands.hybrid_command(aliases=["disconnect", "dc", "disc", "lv", "fuckoff"], description="Potato will leave.")
    async def leave(self, ctx: commands.Context):
        """Potato will leave."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)
        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command", ephemeral=True)

        await player.destroy()
        await ctx.send("Potato has left the channel.", delete_after=15)

    @commands.hybrid_command(aliases=["pla", "p"], description="Play some music!")
    async def play(self, ctx: commands.Context, *, search: str) -> None:
        """Play some music!"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)
        
        channel = ctx.author.voice.channel
        if not channel.permissions_for(ctx.me).connect:
            return await ctx.send("I don't have permission to connect to the voice channel.", ephemeral=True)

        if not (player := ctx.voice_client):
            await ctx.author.voice.channel.connect(cls=Player)
            player: Player = ctx.voice_client
            await player.set_context(ctx=ctx)
        results = await player.get_tracks(search, ctx=ctx)
        if not results:
            embed = discord.Embed(title=f"{search} by {ctx.author.name}.",description="No results were found for your search..", color=0x00ffff)
            return await ctx.send(embed=embed, delete_after=7)

        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                player.queue.put(track)
                
        else:
            track = results[0]
            player.queue.put(track)
            if player.is_playing:
                embed = discord.Embed(description=f"Added {track.title} to the queue.", color=0x00ffff)
                await ctx.send(embed=embed)

        if not player.is_playing:
            await player.do_next()

    @commands.hybrid_command(aliases=["repla"], description="Repeat current song.")
    async def replay(self, ctx: commands.Context) -> None:
        """Replay current song. Add it first in the queue."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)

        if not (player := ctx.voice_client):
            await ctx.author.voice.channel.connect(cls=Player)
            player: Player = ctx.voice_client
            await player.set_context(ctx=ctx)

        if not player.is_playing:
            return await ctx.send("The player is not playing.", ephemeral=True)
        
        current_track = player.current
        player.queue._insert(0, current_track)
        embed = discord.Embed(description=f"{ctx.author.mention} added {current_track.title} to the front of the queue.", color=0x00ffff)
        await ctx.send(embed=embed, delete_after=7)

    @commands.hybrid_command(aliases=["rr"], description="Rickroll the voice channel.")
    async def rickroll(self, ctx: commands.Context) -> None:
        """Rickroll the voice channel."""
        search = "never gonna give you up"
        if not (player := ctx.voice_client):
            await ctx.author.voice.channel.connect(cls=Player)
            player: Player = ctx.voice_client
            await player.set_context(ctx=ctx)

        results = await player.get_tracks(search, ctx=ctx)

        if not results:
            return await ctx.send("No results were found for that search term", delete_after=7)

        if isinstance(results, pomice.Playlist):
            for track in results.tracks:
                player.queue.put(track)
                
        else:
            track = results[0]
            player.queue.put(track)
            if player.is_playing:
                await ctx.send(f"Added {track.title} to the queue.")

        if not player.is_playing:
            await player.do_next()

    @commands.hybrid_command(aliases=["pau", "pa"], description="Pause the currently playing song.")
    async def pause(self, ctx: commands.Context):
        """Pause the currently playing song."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)

        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command.", ephemeral=True)

        if player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            embed = discord.Embed(description=f"{ctx.author.mention} has paused the player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=10)
            player.pause_votes.clear()

            return await player.set_pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            embed = discord.Embed(description="Vote to pause passed. Pausing player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=10)
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            embed = discord.Embed(title=f"Votes: {len(player.pause_votes)}/{required}", description=f"{ctx.author.mention} has voted to pause the player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=10)

    @commands.hybrid_command(aliases=["res", "r"], description="Resume a currently paused player.")
    async def resume(self, ctx: commands.Context):
        """Resume a currently paused player."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)

        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command.", ephemeral=True)

        if not player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            embed = discord.Embed(description=f"{ctx.author.mention} has resumed the player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=10)
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            embed = discord.Embed(description="Vote to resume passed. Resuming player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=10)
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            embed = discord.Embed(title=f"Votes: {len(player.resume_votes)}/{required}", description=f"{ctx.author.mention} has voted to resume the player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=10)

    @commands.hybrid_command(aliases=["n", "nex", "next", "sk"], description="Skip the currently playing song.")
    async def skip(self, ctx: commands.Context):
        """Skip the currently playing song."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)

        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command.", ephemeral=True)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            embed = discord.Embed(description=f"{ctx.author.mention} has skipped the song.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=30)
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            embed = discord.Embed(description=f"{ctx.author.mention} has skipped the song.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=30)
            player.skip_votes.clear()
            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            embed = discord.Embed(description="Vote to skip passed. Skipping song.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=30)
            player.skip_votes.clear()
            await player.stop()
        else:
            embed = discord.Embed(title=f"Votes: {len(player.skip_votes)}/{required}", description=f"{ctx.author.mention} has voted to skip the song.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=15)        

    @commands.hybrid_command(name="stop", description="Stop the player and clear the queue.")
    async def stop(self, ctx: commands.Context):
        """Stop the player and clear the queue."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)

        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command.", ephemeral=True)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            embed = discord.Embed(description=f"{ctx.author.mention} has stopped the player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=30)
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            embed = discord.Embed(description="Vote to stop passed. Stopping the player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=30)
            await player.teardown()
        else:
            embed = discord.Embed(title=f"Votes: {len(player.stop_votes)}/{required}", description=f"{ctx.author.mention} has voted to stop the player.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=15)

    @commands.hybrid_command(aliases=["q", "que"], description="List the queued songs.")
    async def queue(self, ctx: commands.Context):
        """List the queued songs."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)
        
        """List the queued songs."""
        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command", ephemeral=True)

        if not player.is_connected:
            return

        queue_list = []
        for index, track in enumerate(player.queue._queue, start=1):
            queue_list.append(f"{index}. **{track.title}** [Added by {track.requester.mention}]")

        queue_message = "\n".join(queue_list)
        embed = discord.Embed(title="Current Playlist", description=queue_message, color=0x00ffff)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Skip to a specific time in the song.")                    
    async def seek(self, ctx: commands.Context, *, time: int):
        """Skip to a specific time in the song."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)
        
        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command", ephemeral=True)
        
        if not player.is_connected:
            return
        
        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may seek.", ephemeral=True)
        
        if not player.is_playing:
            return await ctx.send("The player is not playing.", ephemeral=True)
        
        if time < 0:
            return await ctx.send("Please enter a positive value.", ephemeral=True)

        await player.seek(time * 1000)
        
        track = player.current
        timp = track.length
        timp_seconds = timp // 1000
        timp_minutes, timp_seconds = divmod(timp_seconds, 60)
        timp_hours, timp_minutes = divmod(timp_minutes, 60)
        timp_days, timp_hours = divmod(timp_hours, 24)
        if timp_days == 0:
            timp_total = "%d:%02d:%02d" % (timp_hours, timp_minutes, timp_seconds)
        else:
            timp_total = "%d:%02d:%02d:%02d" % (timp_days, timp_hours, timp_minutes, timp_seconds)
        if timp_hours == 0:
            timp_total = "%d:%02d" % (timp_minutes, timp_seconds)
        else:
            timp_total = "%d:%02d:%02d" % (timp_hours, timp_minutes, timp_seconds)
        embed = discord.Embed(title=f"Seek (total {timp_total})", description=f"{ctx.author.mention} seeked to {time} seconds.", color=0x00ffff)
        await ctx.send(embed=embed, delete_after=30)

    @seek.error
    async def seek_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a valid time in seconds.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a time in seconds to seek to.", ephemeral=True)
        else:
            await ctx.send("Seek time must be between 0 and the track length.", ephemeral=True)

    @commands.hybrid_command(aliases=["mix", "shuf"], description="Shuffle the players queue.")
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the players queue."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)
        
        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command", ephemeral=True)

        if not player.is_connected:
            return

        if player.queue.qsize() < 3:
            return await ctx.send("The queue is empty. Add some songs to shuffle the queue.", ephemeral=True)

        if self.is_privileged(ctx):
            embed = discord.Embed(description=f"{ctx.author.mention} has shuffled the queue.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=30)
            player.shuffle_votes.clear()
            return player.queue.shuffle()

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            embed = discord.Embed(description="Vote to shuffle passed. Shuffling the queue.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=30)
            player.shuffle_votes.clear()
            player.queue.shuffle()
        else:
            embed = discord.Embed(title=f"{len(player.shuffle_votes)}/{required}", description=f"{ctx.author.mention} has voted to shuffle the queue.", color=0x00ffff)
            await ctx.send(embed=embed, delete_after=15)

    @commands.hybrid_command(aliases=["v", "vol"], description="Change the player volume (from 0 to 100).")
    async def volume(self, ctx: commands.Context, *, vol: int):
        """Change the volume of the player."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.", ephemeral=True)
        
        if not (player := ctx.voice_client):
            return await ctx.send("You must have the bot in a channel in order to use this command.", ephemeral=True)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the volume.", ephemeral=True)

        if not 0 < vol < 101:
            return await ctx.send("Please enter a value between 1 and 100.", ephemeral=True)

        await player.set_volume(vol)

        embed = discord.Embed(title="Volume", description=f"{ctx.author.mention} set the volume to **{vol}**%", color=0x00ffff)
        await ctx.send(embed=embed, delete_after=30)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))