import discord
from discord.ext import commands

COMMAND_PREFIX = '39!'
INTENTS = discord.Intents.all()
COGS_FILE = 'cogs.txt'
TOKEN_FILE = 'token.txt'
FILE_MISSING_ERROR = ('Error opening %s for reading, '
                      'please check this file exists.')


class Robot39(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX, intents=INTENTS)
        
        # Read cogs list from file
        try:
            cogs_txt = open(COGS_FILE, "r")

        except OSError:
            print(FILE_MISSING_ERROR % COGS_FILE)
            raise SystemExit

        cogs = cogs_txt.read().splitlines()
        cogs_txt.close()

        # Load all cogs that were listed in file
        for cog in cogs:
            try:
                self.load_extension('cogs.%s' % cog)
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
            token_txt = open(TOKEN_FILE, "r")
            
        except OSError:
            print(FILE_MISSING_ERROR % TOKEN_FILE)
            raise SystemExit

        TOKEN = token_txt.read()
        token_txt.close()

        # Remove default help command and start the bot
        self.remove_command('help')
        self.run(TOKEN)
    
    # Make database connection accessible across the entire bot
    @property
    def database(self):
        return self.get_cog('Database')


Robot39()