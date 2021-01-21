import discord
from discord.ext import commands

# Set bot intents and command prefix
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="39!", intents=intents)

# Read cogs list from file
try:
    cogs_txt = open("cogs.txt", "r")
except OSError:
    print("Error opening cogs.txt for reading, please check this file exists.")
    raise SystemExit
cogs = cogs_txt.read().splitlines()
cogs_txt.close()

# Load all cogs that were listed in file
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

# Read token from file
try:
    token_txt = open("token.txt", "r")
except OSError:
    print("Error opening token.txt for reading, please check this file exists.")
    raise SystemExit
TOKEN = token_txt.read()
token_txt.close()

# Remove default help command and start the bot
bot.remove_command('help')
bot.run(TOKEN)