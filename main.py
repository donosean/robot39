import discord
from discord.ext import commands

#set intents and bot command prefix
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="39!", intents=intents)

#read cogs list from file
try:
    cogs_txt = open("cogs.txt", "r")

except OSError:
    print("Error opening cogs.txt for reading, please check this file exists.")
    raise SystemExit

cogs = cogs_txt.read().splitlines()
cogs_txt.close()

#load all cogs from cogs[] list
for cog in cogs:  
    try:
        bot.load_extension('cogs.%s' % cog)
        print("Loaded cog: %s" % cog)

    except commands.ExtensionNotFound:
        print("Cog '%s' could not be found." % cog)

    except commands.ExtensionAlreadyLoaded:
        print("Cog '%s' is already loaded." % cog)

    except commands.NoEntryPointError:
        print("Cog '%s' has no setup function." % cog)

    except commands.ExtensionFailed:
        print("Cog '%s' had a setup function error." % cog)

#read token from file
try:
    token_txt = open("token.txt", "r")

except OSError:
    print("Error opening token.txt for reading, please check this file exists.")
    raise SystemExit

TOKEN = token_txt.read()
token_txt.close()

#remove ugly default help command
bot.remove_command('help')

#finally run the bot
bot.run(TOKEN)