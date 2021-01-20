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
    # Sends the same text to the terminal and context channel/DM
    async def say(self, ctx, text: str):
        try:
            await ctx.reply(text)

        except discord.Forbidden:
            print("owner: Missing permissions to reply.")
        
        print("owner: %s" % text)

    # Reloads/loads/unloads a cog depending on given CogAction
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
    
    # Sends message to a channel; can be a reply to another
    # message if a message ID is provided and reply = True
    async def send(self, ctx, channel: Union[int, discord.TextChannel],
                   message: str, msg_id: int = None, reply: bool = False):
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
                reply_msg = await channel.fetch_message(msg_id)
                await self.say(ctx, "Replied to message by %s in %s."
                               % (reply_msg.author, channel.name))
                await reply_msg.reply(message)
        
        except discord.NotFound:
                await self.say(ctx, "Message not found.")
        
        except discord.HTTPException:
                await self.say(ctx, "Retrieving the message failed.")

        except discord.Forbidden:
            await self.say(ctx, "Missing permissions to fetch/send message.")
        
    ### !--- CHECKS & COMMANDS ---! ###
    # Restricts all commands in this cog to the owner of the bot
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        else:
            raise commands.NotOwner(
                'owner: %s does not own this bot.' % ctx.author)

    # Reloads a cog that is already loaded
    @commands.command(name="reload_cog", aliases=["reload"])
    async def reload_cog(self, ctx, cog: str):
        await self.manage_cog(ctx, cog, CogAction.reload)

    # Loads a cog that hasn't been loaded
    @commands.command(name="load_cog", aliases=["load"])
    async def load_cog(self, ctx, cog: str):
        await self.manage_cog(ctx, cog, CogAction.load)

    # Unloads a cog that has already been loaded
    @commands.command(name="unload_cog", aliases=["unload"])
    async def unload_cog(self, ctx, cog: str):
        await self.manage_cog(ctx, cog, CogAction.unload)
    
    # Sends a message to a channel given by channel ID/mention
    @commands.command(name="send_message", aliases=["send", "message"])
    async def send_message(self, ctx, channel: Union[int, discord.TextChannel],
                           *msg):
        # Join *msg arguments into one string and pass on to send method
        message = ' '.join(msg)
        await self.send(ctx, channel, message)
    
    # Sends a reply to a message given by channel ID/mention and message ID
    @commands.command(name="send_reply", aliases=["reply"])
    async def send_reply(self, ctx, channel: Union[int, discord.TextChannel],
                         msg_id: int, *msg):
        # Join *msg arguments into one string and pass on to send method
        message = ' '.join(msg)
        await self.send(ctx, channel, message, msg_id = msg_id, reply = True)

    # Adds a reaction to a message given by channel ID/mention,
    # message ID and emoji as string
    @commands.command(name="add_reaction", aliases=["react"])
    async def add_reaction(self, ctx, channel: Union[int, discord.TextChannel],
                           msg_id: int, react_emoji: str):
        # Get channel if only a channel ID is given
        if type(channel) == int:
            channel = self.bot.get_channel(channel)
        if not channel:
            await self.say(ctx, "Channel not found.")
            return

        # Get the message from the ID and add the reaction
        try:
            react_msg = await channel.fetch_message(msg_id)
            await react_msg.add_reaction(react_emoji)
            await self.say(ctx, "Reaction added to message by %s in %s."
                           % (react_msg.author, channel.name))

        except discord.Forbidden:
            await self.say(ctx, "Missing permissions to add reaction.")

        except discord.NotFound:
            await self.say(ctx, "Emoji or message not found.")

        except discord.InvalidArgument:
            await self.say(ctx, "Invalid emoji parameter given.")

        except discord.HTTPException:
            await self.say(ctx, "Failed to add reaction due to HTTP exception,"\
                           " or potentially nonexistant emoji.")


def setup(bot):
    bot.add_cog(Owner(bot))