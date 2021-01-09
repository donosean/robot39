import discord
from discord.ext import commands

class AutoRole(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot
        
        ### !--- CONFIGURABLE ---! ###
        self.autorole_id = 765256868041850911

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_member_join(self, member):
        #fetch role using role id
        autorole = member.guild.get_role(self.autorole_id)

        #only continue if role actually exists
        if not autorole:
            print("autorole: Role could not be found, possible incorrect ID given.")
            return

        #finally, try add the role to the new member
        try:
            await member.add_roles(autorole)
            print("autorole: Role '%s' added to %s." % (autorole.name, member))

        except discord.Forbidden:
            print("autorole: Missing permissions to add role '%s' to %s." % (autorole.name, member))

        except discord.HTTPException:
            print("autorole: Failed to add role '%s' to %s." % (autorole.name, member))

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(AutoRole(bot))