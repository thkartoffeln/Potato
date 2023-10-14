import discord
from discord.ext import commands
from discord import app_commands

class InviteButton(discord.ui.View):
    def __init__(self):
        super().__init__()

class Info(commands.Cog, description="Info commands."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.hybrid_command(name="invite", description="Invite Potato to your server.")
    async def invite_command(self, ctx: commands.Context):
        """Invite Potato to your server."""
        embed=discord.Embed(title="🥔", description="Invite Potato to your server.", color=0x00ffff)
        view=InviteButton()
        view.add_item(discord.ui.Button(label="Click me!", style=discord.ButtonStyle.blurple, url="https://discord.com/api/oauth2/authorize?client_id=411891117873823744&permissions=0&scope=bot%20applications.commands"))
        await ctx.send(embed=embed, view=view, ephemeral=True)
    
    @commands.hybrid_command(name="help", description="Displays the help message.")
    async def help_command(self, ctx: commands.Context):
        """Displays the help message."""
        embed = discord.Embed(title="Bot Help", description="List of available commands:", color=0x00ffff)
        embed.add_field(name="Info", value="help, invite, avatar", inline=False)
        embed.add_field(name="Music (/music ...)", value="play, stop, pause, resume, skip, queue, shuffle, volume, replay, join, leave, seek (in seconds) ", inline=False)
        embed.add_field(name="Various (/dev ...)", value="uptime, status", inline=False)
        embed.set_footer(text=f"Version {self.bot.versiune}")
        ###for command in self.bot.commands:
        ###    embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)

    

async def setup(bot):
    await bot.add_cog(Info(bot))