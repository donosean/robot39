import discord
from discord.ext import commands


class Quotes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.staff_roles = ["Secret Police"]
        self.quotes_channel_id = 797182745050087455

    ### !--- METHODS ---! ###
    # Sends the same text to the terminal and context channel
    async def say(self, ctx, text: str):
        try:
            await ctx.reply(text)

        except discord.Forbidden:
            print("quotes: Missing permissions to reply.")
        
        print("quotes: %s" % text)

    ### !--- CHECKS & COMMANDS ---! ###
    # Restricts all commands in this cog to specific checks
    async def cog_check(self, ctx):
        # Allow bot owner and server admins
        if (await ctx.bot.is_owner(ctx.author)
                or ctx.author.guild_permissions.administrator):
            return True
        
        # Also allow users with roles listed in self.staff_roles
        quotes_channel = self.bot.get_channel(self.quotes_channel_id)
        staff_roles = [discord.utils.get(quotes_channel.guild.roles, name=role)
                       for role in self.staff_roles]

        return any(role in staff_roles for role in ctx.author.roles)
    
    # Posts an embed to the quotes channel, containing a quoted message 
    # obtained from a channel mention and a message ID
    @commands.command(name="add_quote", aliases=["quote"])
    @commands.guild_only()
    async def add_quote(self, ctx, channel_mention: discord.TextChannel,
                        message_id):
        # Get the message from the mentioned channel using the message ID
        try:
            message = await channel_mention.fetch_message(message_id)
        
        except discord.Forbidden:
            await self.say(ctx, "Missing permissions to fetch message.")
            return

        except discord.NotFound:
            await self.say(ctx, "Message not found.")
            return
        
        except discord.HTTPException:
            await self.say(ctx, "Retrieving the message failed.")
            return

        # Check if message contains actual text content
        if len(message.content) == 0:
            await self.say(ctx, "Message contains no quotable text content.")
            return

        # Date of message creation, formatted like "1 January 2021"
        msg_date = message.created_at.strftime("%d %B %Y")

        # Create embed to post in quotes channel
        embed=discord.Embed(title="Quote", color=0x80ffff)
        embed.set_thumbnail(url=message.author.avatar_url)
        embed.add_field(name=message.content, value="-- %s, [%s](%s)"
                        % (message.author.mention, msg_date, message.jump_url),
                        inline=False)

        # Get quotes channel and send the embed
        try:
            quotes_channel = self.bot.get_channel(self.quotes_channel_id)
            await quotes_channel.send(embed=embed)
            await self.say(ctx, "Added a quote by %s." % (message.author))

        except discord.Forbidden:
            await self.say(ctx, "Missing permissions to post quote.")

        except discord.HTTPException:
            await self.say(ctx, "Posting the quote failed.")


def setup(bot):
    bot.add_cog(Quotes(bot))