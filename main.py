### !--- IMPORTS ---! ###
import discord
from discord.ext import commands, tasks

### !--- SETTINGS ---! ###
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="39!", intents=intents)

### !--- COGS ---! ###
"""
cogs = [
    'catwalk',
    'duel',
    'events',
    'logging',
    'owner',
    #'welcome'
]
"""
cogs_txt = open("cogs.txt", "r")
cogs = cogs_txt.read().splitlines()

### !--- EXECUTION CODE ---! ###
#load all cogs from cogs[] list
for cog in cogs:  
    bot.load_extension('cogs.%s' % cog)
    print("Loaded cog: %s" % cog)

#remove ugly default help command
bot.remove_command('help')

#read token from file
token_txt = open("token.txt", "r")
TOKEN = token_txt.read()
token_txt.close()

#finally run the bot
bot.run(TOKEN)