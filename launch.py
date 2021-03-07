import discord
from robot39 import Robot39

COMMAND_PREFIX = '39!'
INTENTS = discord.Intents.all()
COGS_FILE = 'cogs.txt'
TOKEN_FILE = 'token.txt'

robot39 = Robot39(COMMAND_PREFIX, INTENTS, COGS_FILE, TOKEN_FILE)
robot39.start_bot()