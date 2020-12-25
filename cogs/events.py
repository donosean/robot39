import discord
from discord.ext import commands, tasks

class Events(commands.Cog):

    #---INIT---
    def __init__(self, bot):
        self.bot = bot
        self.print_messages = False

    #---EVENTS---
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot logged in as %s" % self.bot.user)

        #now playing status
        await self.bot.change_presence(activity=discord.Game("Hatsune Miku: Project DIVA Future Tone"))

    @commands.Cog.listener()
    async def on_message(self, message):
        #ignore messages sent by this or other bots
        if message.author.bot:
            return

        #prints all messages sent by users to the console
        if self.print_messages:
            print("%s in #%s: %s" % (message.author, message.channel, message.content))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        #generic error to catch all command exceptions
        print("%s: %s" %(ctx.message.author, e))

    @commands.Cog.listener()
    async def on_command(self, ctx):
        #print all used commands to terminal
        print("%s: %s" %(ctx.message.author, ctx.message.content))
    
    #---CHECK & COMMANDS---
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        else:
            raise commands.NotOwner('You do not own this bot.')

    @commands.command()
    async def messages(self, ctx):
        self.print_messages = True if not self.print_messages else False
        print("events: Print messages enabled." if self.print_messages else "events: Print messages disabled.")

#---SETUP---
def setup(bot):
    bot.add_cog(Events(bot))