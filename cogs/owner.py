import discord
from discord.ext import commands

class Owner(commands.Cog):

    #---INIT---
    def __init__(self, bot):
        self.bot = bot

    #---CHECK & COMMANDS---
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        else:
            raise commands.NotOwner('You do not own this bot.')

    @commands.command()
    async def reload(self, ctx, cog):
        try:
            self.bot.reload_extension("cogs.%s" % cog)
            print("Reloaded cog: %s" % cog)
            await ctx.send("Reloaded: %s" % cog)
        except commands.ExtensionNotLoaded:
            print("Error: Cog %s could not be reloaded." % cog)
            await ctx.send("Unable to reload %s, check the name and try again." % cog)

    @commands.command()
    async def load(self, ctx, cog):
        try:
            self.bot.load_extension("cogs.%s" % cog)
            print("Loaded cog: %s" % cog)
            await ctx.send("Loaded: %s" % cog)
        except commands.ExtensionNotLoaded:
            print("Error: Cog %s could not be loaded." % cog)
            await ctx.send("Unable to load %s, check the name and try again." % cog)

    @commands.command()
    async def unload(self, ctx, cog):
        try:
            self.bot.unload_extension("cogs.%s" % cog)
            print("Unloaded cog: %s" % cog)
            await ctx.send("Unloaded: %s" % cog)
        except commands.ExtensionNotLoaded:
            print("Error: Cog %s could not be unloaded." % cog)
            await ctx.send("Unable to unload %s, check the name and try again." % cog)
    
    @commands.command() 
    @commands.dm_only()
    async def echo(self, ctx, channel_id: int, *msg):    
        channel = self.bot.get_channel(channel_id)
        if channel:
            message = ' '.join(msg)
            await channel.send(message)
            print("Sent message to %s." % channel.name)
        else:
            await ctx.send("Channel not found.")
    
    @commands.command()
    async def print_emoji(self, ctx):
        for emoji in ctx.guild.emojis:
            print(emoji)

#---SETUP---
def setup(bot):
    bot.add_cog(Owner(bot))