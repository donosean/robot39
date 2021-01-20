import discord
from discord.ext import commands


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_command(self, ctx):
        print("events: %s used a command: %s"
              % (ctx.message.author, ctx.message.content))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        print("events: %s: %s" % (ctx.message.author, e))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print("events: Bot joined server %s (%s)" % (guild.name, guild.id))
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print("events: Bot was removed from server %s (%s)"
              % (guild.name, guild.id))

    @commands.Cog.listener()
    async def on_ready(self):
        print("events: Bot logged in as %s" % self.bot.user)
        print("events: Bot is currently a member of %s server(s)"
              % len(self.bot.guilds))

        try:
            await self.bot.change_presence(
                    activity=discord.Game(
                        "Hatsune Miku: Project DIVA Future Tone"))
        
        except discord.InvalidArgument:
            print("events: Invalid argument given for changing bot presence")


def setup(bot):
    bot.add_cog(Events(bot))