import discord
import os
import datetime
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='potato ', owner_id = 254198214415220738, intents=intents)
bot.remove_command('help')
bot.versiune = '0.0.2'

@bot.event
async def on_ready():
    print(
            "\n +--------------------------------------------+"
            "\n |       PotatoBOT - Discord Python BOT       |"
            "\n | (c) 2023 Kartoffeln (LionBlood Community)  |"
            "\n +--------------------------------------------+\n"
         )
    print(f'\n\nLogged in as: {bot.user.name}')
    print(f'ID {bot.user.id}')
    print(f'Version: {bot.versiune}')
    print('Done. Bot logged in.')
    bot.start_time = datetime.datetime.now()
    bot_status = discord.Activity(type=discord.ActivityType.watching, name="/help | 🥔")
    await bot.change_presence(status=discord.Status.dnd, activity=bot_status)
    
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            name = file[:-3]
            await bot.load_extension("cogs.{}".format(name))
            
    await bot.tree.sync()

@bot.tree.command(name="avatar",description="Get user avatar.")
async def avatar(interaction:discord.Interaction,member:discord.Member):
    await interaction.response.send_message(member.display_avatar)
    


bot.run('NDExODkxMTE3ODczODIzNzQ0.G-YwEo.2wUxhPYgJEKYwDCThkDFjcfWAxGqV1qHaE1Ujg')