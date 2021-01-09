import discord
from discord.ext import commands, tasks

class Events(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot
        self.print_messages = False

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_command(self, ctx):
        #print all used commands to terminal
        print("events: %s used a command: %s" % (ctx.message.author, ctx.message.content))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        #generic error to catch all command exceptions
        print("%s: %s" % (ctx.message.author, e))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        #print whenever bot joins a server
        print("Bot joined server %s (%s)." % (guild.name, guild.id))
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        #print whenever bot leaves or is kicked/banned from a server
        print("Bot was removed from server %s (%s)." % (guild.name, guild.id))

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot logged in as %s" % self.bot.user)
        print("Bot is currently a member of %s server(s)." % len(self.bot.guilds))

        #now playing status
        try:
            await self.bot.change_presence(activity=discord.Game("Hatsune Miku: Project DIVA Future Tone"))
        
        except discord.InvalidArgument:
            print("events: Invalid argument given for changing bot presence.")

    @commands.Cog.listener()
    async def on_message(self, message):
        #ignore messages sent by this or other bots
        if message.author.bot:
            return

        #prints all messages sent by users to the console
        if self.print_messages:
            print("%s in %s: %s" % (message.author, message.channel, message.content))

    ### !--- CHECKS & COMMANDS ---! ###
    async def cog_check(self, ctx):
        #all commands are only accessible to the owner of the bot
        if await ctx.bot.is_owner(ctx.author):
            return True

        else:
            raise commands.NotOwner('events: %s does not own this bot.' % ctx.author)

    #toggles self.print_messages to enable/disable printing all sent messages to terminal via on_message()
    @commands.command()
    async def toggle_print_messages(self, ctx):
        self.print_messages = True if not self.print_messages else False
        print("events: Printing messages " + ("enabled." if self.print_messages else "disabled."))

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Events(bot))