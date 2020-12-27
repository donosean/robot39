### !--- IMPORTS ---! ###
import discord
from discord.ext import commands, tasks

### !--- SETTINGS ---! ###
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="39!", intents=intents)

### !--- EXECUTION CODE ---! ###
#read cogs list from file
cogs_txt = open("cogs.txt", "r")
cogs = cogs_txt.read().splitlines()

#load all cogs from cogs[] list
for cog in cogs:  
    bot.load_extension('cogs.%s' % cog)
    print("Loaded cog: %s" % cog)

#read token from file
token_txt = open("token.txt", "r")
TOKEN = token_txt.read()
token_txt.close()

#remove ugly default help command
bot.remove_command('help')

#finally run the bot
bot.run(TOKEN)