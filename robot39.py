import discord
from discord.ext import commands


FILE_MISSING_ERROR = ('Error opening %s for reading, '
                      'please check this file exists.')


class Robot39(commands.Bot):

    def __init__(self, prefix, intents, cogs_file, token_file):
        super().__init__(command_prefix=prefix, intents=intents)
        
        # Read cogs list from file
        try:
            cogs_txt = open(cogs_file, "r")

        except OSError:
            print(FILE_MISSING_ERROR % cogs_file)
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
            token_txt = open(token_file, "r")
            
        except OSError:
            print(FILE_MISSING_ERROR % token_file)
            raise SystemExit

        self.token = token_txt.read()
        token_txt.close()

        # Remove default help command and start the bot
        self.remove_command('help')
    
    # Make database connection accessible across the entire bot
    @property
    def database(self):
        return self.get_cog('Database')
    
    def start_bot(self):
        self.run(self.token)


class Cog(commands.Cog):

    def __init__(self, bot):
        super().__init__()

    def log(self, text):
        print("%s: %s" % (self.qualified_name, text))

    async def say(self, ctx, text: str):
        try:
            await ctx.reply(text)

        except discord.Forbidden:
            self.log('Missing permissions to reply.')
        
        self.log(text)