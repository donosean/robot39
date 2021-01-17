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

        #check for nickname change
        if before.nick == after.nick:
            return

        #check if new nickname matches bot's current nickname in that server
        if after.nick == after.guild.me.nick:
            #and if so, change the nickname
            try:
                member = after.guild.get_member(after.id)
                await member.edit(nick="Jebaited")
                print("nomimic: Caught matching nickname, reverted for user %s." % member)
            
            except discord.errors as e:
                print("nomimic: Error changing nickname -- %s" % e)

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(NoMimic(bot))