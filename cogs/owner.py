import discord
import asyncio
import time
import datetime
from discord.ext import commands
from discord import app_commands

class Owner(commands.GroupCog, name="dev", description="Owner commands."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.hybrid_command(name="status", description="Show Potato stats.")
    async def status(self, ctx):
        start_time = time.monotonic()
        message = await ctx.send("Loading status...")
        end_time = time.monotonic()
        ping = (end_time - start_time) * 100
        bot_latency = round(self.bot.latency * 100)

        embed = discord.Embed(title="Status", description="🥔", color=0x00ffff)
        embed.add_field(name="Bot latency", value=f"Bot latency: {bot_latency} ms.", inline=True)
        embed.add_field(name="API latency", value=f"API latency: {ping:.0f} ms.", inline=True)
        embed.add_field(name="Uptime", value=str(datetime.datetime.now() - self.bot.start_time).split('.')[0], inline=True)
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        embed.add_field(name="Cogs", value=len(self.bot.cogs), inline=True)
        embed.set_footer(text=f"Version: {self.bot.versiune}")
        await message.edit(content=None, embed=embed)

    @commands.hybrid_command(name="uptime", description="Show Potato uptime.")
    async def uptime(self, ctx):
        embed = discord.Embed(title="Uptime", description=f"🥔 {str(datetime.datetime.now() - self.bot.start_time).split('.')[0]}", color=0x00ffff)
        await ctx.send(embed=embed, ephemeral=True)


    @commands.hybrid_command(name='unload', description="Unload a module.")
    @commands.is_owner()
    async def cunload(self, ctx, *, cog: str):
        try:
            await self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'**`Unloaded {cog}.`**')

    @cunload.error
    async def cunload_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not **thkartoffeln**.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to unload.")

    @commands.hybrid_command(name='load', description="Load a module.")
    @commands.is_owner()
    async def cload(self, ctx, *, cog: str):
        try:
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'**`Loaded {cog}.`**')       

    @cload.error
    async def cload_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not **thkartoffeln**.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to load.")

    @commands.hybrid_command(name='reload', description="Reload a module.")
    @commands.is_owner()
    async def creload(self, ctx, *, cog: str):
        try:
            await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'**`Reloaded {cog}.`**')

    @creload.error
    async def creload_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not **thkartoffeln**.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to reload.")

    @commands.hybrid_command(name="ping", description="Verify ping.")
    @commands.is_owner()
    async def ping(self, ctx):
        start_time = time.monotonic()
        message = await ctx.send("Pinging...")
        end_time = time.monotonic()
        ping = (end_time - start_time) * 100
        bot_latency = round(self.bot.latency * 100)
        await message.edit(content=f"Pong! Bot latency: {bot_latency} ms, API latency: {ping:.0f} ms.")

    @commands.hybrid_command(name='shutdown', description="Shutdown the bot.")
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send('Shutting down in 5 seconds..')
        await asyncio.sleep(5)
        await ctx.send('Done.')
        await asyncio.sleep(2)
        await self.bot.close()

    @commands.hybrid_command(name="sync", description="Sync all commands.")
    @commands.is_owner()
    async def sync(self, ctx):
        await ctx.send("Syncing commands...")
        await self.bot.tree.sync()
        await ctx.send("Done.")


    @ping.error
    async def ping_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not **thkartoffeln**.")

    @shutdown.error
    async def shutdown_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not **thkartoffeln**.")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("An error occurred while processing the command.")
    
    @sync.error
    async def sync_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("You are not **thkartoffeln**.")

async def setup(bot):
    await bot.add_cog(Owner(bot))