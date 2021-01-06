import discord
from discord.ext import commands

class Owner(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot

    ### !--- CHECKS & COMMANDS ---! ###
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        else:
            raise commands.NotOwner('owner: You do not own this bot.')

    @commands.command()
    async def reload(self, ctx, cog):
        try:
            self.bot.reload_extension("cogs.%s" % cog)
            print("owner: Reloaded %s" % cog)
            await ctx.send("Reloaded %s" % cog)
        except commands.ExtensionNotLoaded:
            print("owner: Error -- %s could not be reloaded." % cog)
            await ctx.send("Unable to reload %s, check the name and try again." % cog)

    @commands.command()
    async def load(self, ctx, cog):
        try:
            self.bot.load_extension("cogs.%s" % cog)
            print("owner: Loaded %s" % cog)
            await ctx.send("Loaded %s" % cog)
        except commands.ExtensionNotLoaded:
            print("owner: Error -- %s could not be loaded." % cog)
            await ctx.send("Unable to load %s, check the name and try again." % cog)

    @commands.command()
    async def unload(self, ctx, cog):
        try:
            self.bot.unload_extension("cogs.%s" % cog)
            print("owner: Unloaded %s" % cog)
            await ctx.send("Unloaded %s" % cog)
        except commands.ExtensionNotLoaded:
            print("owner: Error -- %s could not be unloaded." % cog)
            await ctx.send("Unable to unload %s, check the name and try again." % cog)
    
    @commands.command() 
    @commands.dm_only()
    async def echo(self, ctx, channel_id: int, *msg):    
        channel = self.bot.get_channel(channel_id)
        if channel:
            message = ' '.join(msg)
            await channel.send(message)
            print("owner: Sent message to %s." % channel.name)
        else:
            await ctx.send("Channel not found.")
    
    @commands.command()
    async def print_emoji(self, ctx):
        for emoji in ctx.guild.emojis:
            print(emoji)

    @commands.command()
    async def add_reaction(self, ctx, react_channel: discord.TextChannel, msg_id: int, react_emoji: str):
        try:
            react_msg = await react_channel.fetch_message(msg_id)
            await react_msg.add_reaction(react_emoji)
            print("owner: Added reaction to message in %s." % react_channel)
        except:
            print("owner: Error adding reaction to specified message.")

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Owner(bot))