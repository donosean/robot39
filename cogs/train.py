import discord
from discord.ext import commands

class Train(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot

        ### !--- CONFIGURABLE ---! ###
        self.train_channel_id = 765064651796119552 #get this by right clicking on your #welcome channel and clicking "Copy ID"

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_message(self, message):
        #ignore messages sent by this or other bots
        if message.author.bot or not message.channel.id == self.train_channel_id:
            return
        
        train_channel = self.bot.get_channel(self.train_channel_id)
        print(train_channel.last_message_id)

    ### !--- CHECKS & COMMANDS ---! ###
    @commands.command()
    @commands.is_owner()
    @commands.dm_only()
    async def train(self, ctx):
        channel = self.bot.get_channel(self.train_channel_id)
        async for message in channel.history(limit=1):
            print(message.content)

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Train(bot))