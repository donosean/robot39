import robot39
import discord
from discord.ext import commands


class Events(robot39.Cog):

    def __init__(self, bot):
        self.bot = bot

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.log("%s used a command: %s"
                 % (ctx.message.author, ctx.message.content))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        self.log("%s: %s" % (ctx.message.author, e))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.log("Bot joined server %s (%s)" % (guild.name, guild.id))
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.log("Bot was removed from server %s (%s)" % (guild.name, guild.id))

    @commands.Cog.listener()
    async def on_ready(self):
        self.log("Bot logged in as %s" % self.bot.user)
        self.log("Bot is currently a member of %s server(s)"
                 % len(self.bot.guilds))

        try:
            await self.bot.change_presence(
                    activity=discord.Game(
                        "Hatsune Miku: Project DIVA Future Tone"))
        
        except discord.InvalidArgument:
            self.log("Invalid argument given for changing bot presence")


def setup(bot):
    bot.add_cog(Events(bot))