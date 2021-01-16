import discord
from discord.ext import commands

class NoMimic(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        #ignore bot account updates
        if after.bot:
            return

        #check if new nickname matches bot's current nickname in that server
        if after.nick == after.guild.me.nick:
            #and if so, revert the nickname change
            try:
                await after.edit(nick="Jebaited")
                print("nomimic: Caught matching nickname, reverted for user %s." % after)
            
            except discord.Forbidden:
                print("nomimic: Missing permissions to revert nickname for %s." % after)

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(NoMimic(bot))