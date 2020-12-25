import discord
from discord.ext import commands, tasks

class AutoRole(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot
        
        ### !--- CONFIGURABLE ---! ###
        self.autorole = 765256868041850911

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_member_join(self, member):
        autorole = member.guild.get_role(self.autorole)
        await member.add_roles(autorole)

        print("autorole: %s added to %s" % (autorole.name, member))

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(AutoRole(bot))