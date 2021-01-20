import discord
from discord.ext import commands

from enum import Enum
from typing import Union


class CogAction(Enum):
    reload = 'reload'
    load = 'load'
    unload = 'unload'


class Owner(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    ### !--- METHODS ---! ###
    # Send the same text to the terminal and context channel/DM
    async def say(self, ctx, text: str):
        try:
            await ctx.reply(text)

        except discord.Forbidden:
            print("owner: Missing permissions to reply.")
        
        print("owner: %s" % text)

    # Reload/load/unload cog depending on given CogAction
    async def manage_cog(self, ctx, cog: str, action: CogAction):
        try:
            if action == CogAction.reload:
                self.bot.reload_extension("cogs.%s" % cog)
                await self.say(ctx, "Cog '%s' has been reloaded." % cog)

            elif action == CogAction.load:
                self.bot.load_extension("cogs.%s" % cog)
                await self.say(ctx, "Cog '%s' has been loaded." % cog)

            elif action == CogAction.unload:
                self.bot.unload_extension("cogs.%s" % cog)
                await self.say(ctx, "Cog '%s' has been unloaded." % cog)
        
        except commands.ExtensionNotLoaded:
            await self.say(ctx, "Cog '%s' is not loaded." % cog)

        except commands.ExtensionNotFound:
            await self.say(ctx, "Cog '%s' could not be found." % cog)

        except commands.ExtensionAlreadyLoaded:
            await self.say(ctx, "Cog '%s' is already loaded." % cog)

        except commands.NoEntryPointError:
            await self.say(ctx, "Cog '%s' has no setup function." % cog)

        except commands.ExtensionFailed:
            await self.say(ctx, "Cog '%s' had a setup function error." % cog)
    
    # Send message to a channel; can be a reply to another
    # message if a message ID is provided and reply = True
    async def send(self, ctx, channel: Union[int, discord.TextChannel],
                   message: str, message_id: int = None, reply: bool = False):
        # Get channel if only a channel ID is given
        if type(channel) == int:
            channel = self.bot.get_channel(channel)
        if not channel:
            await self.say(ctx, "Channel not found.")
            return

        try:
            # Send message to the given channel
            if not reply:
                await channel.send(message)
                await self.say(ctx, "Sent message to %s." % channel.name)

            # Get the message from the given message ID and send the reply
            else:
                reply_msg = await channel.fetch_message(message_id)
                await self.say(ctx, "Replied to message by %s in %s."
                               % (reply_msg.author, channel.name))
                await reply_msg.reply(message)
        
        except discord.NotFound:
                await self.say(ctx, "Message not found.")

        except discord.Forbidden:
            await self.say(ctx, "Missing permissions to send message.")
        
    ### !--- CHECKS & COMMANDS ---! ###
    async def cog_check(self, ctx):
        #all commands are only accessible to the owner of the bot
        if await ctx.bot.is_owner(ctx.author):
            return True

        else:
            raise commands.NotOwner('owner: %s does not own this bot.' % ctx.author)

    #unloads then re-loads a cog that has been loaded
    @commands.command()
    async def reload_cog(self, ctx, cog: str):
        await self.manage_cog(ctx, cog, CogAction.reload)

    #loads a cog that hasn't been loaded
    @commands.command()
    async def load_cog(self, ctx, cog: str):
        await self.manage_cog(ctx, cog, CogAction.load)

    #unloads a cog that has been loaded
    @commands.command()
    async def unload_cog(self, ctx, cog: str):
        await self.manage_cog(ctx, cog, CogAction.unload)
    
    #sends a message to a channel given by channel id/mention
    @commands.command()
    async def send_message(self, ctx, channel: Union[int, discord.TextChannel], *msg):
        #create the message string from what was passed with the command
        message = ' '.join(msg)
        await self.send(ctx, channel, message)
    
    #sends a reply to a message given by channel id/mention and message id
    @commands.command()
    async def send_reply(self, ctx, channel: Union[int, discord.TextChannel], msg_id: int, *msg):
        #create the message string from what was passed with the command
        message = ' '.join(msg)
        await self.send(ctx, channel, message, msg_id = msg_id, reply = True)

    #adds a reaction to a message given by channel mention, message id and emoji as string
    @commands.command()
    async def add_reaction(self, ctx, channel: Union[int, discord.TextChannel], msg_id: int, react_emoji: str):
        #fetch channel object if only channel id is given
        if type(channel) == int:
            channel = self.bot.get_channel(channel)
        
        #only continue if valid channel is given
        if not channel:
            await self.say(ctx, "Channel not found.")
            return

        #fetch the message from the given message id
        react_msg = None #avoids 'possibly unbound' warning
        try:
            react_msg = await channel.fetch_message(msg_id)
        
        except discord.NotFound:
            await self.say(ctx, "Message not found.")

        #finally, add the reaction using the given emoji
        try:
            await react_msg.add_reaction(react_emoji)
            await self.say(ctx, "Reaction added to message by %s in %s." % (react_msg.author, channel.name))

        except discord.HTTPException:
            await self.say(ctx, "Failed to add reaction due to HTTP exception, or potentially nonexistant emoji.")

        except discord.Forbidden:
            await self.say(ctx, "Missing permissions to add reaction.")

        except discord.NotFound:
            await self.say(ctx, "Emoji or message not found.")

        except discord.InvalidArgument:
            await self.say(ctx, "Invalid emoji parameter given.")
        
### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Owner(bot))