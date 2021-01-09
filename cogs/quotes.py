import discord
from discord.ext import commands

class Quotes(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot
        self.staff_roles = ["Secret Police"]
        self.quotes_channel_id = 797182745050087455

    ### !--- CHECKS & COMMANDS ---! ###
    async def cog_check(self, ctx):
        if ctx.guild == None and ctx.bot.is_owner(ctx.author):
            return True
        
        quotes_channel =  self.bot.get_channel(self.quotes_channel_id)
        staff_roles = [discord.utils.get(quotes_channel.guild.roles, name=role) for role in self.staff_roles]

        if any(role in staff_roles for role in ctx.author.roles):
            return True
        else:
            return False

    @commands.command()
    @commands.guild_only()
    async def add_quote(self, ctx, channel_mention: discord.TextChannel, message_id):
        message = await channel_mention.fetch_message(message_id)

        #check message contains actual text content
        if len(message.content) > 0:
            msg_content = message.content
        else:
            await ctx.send("Message contains no quotable text content.")
            print("quotes: Message contains no quotable text content.")
            return

        msg_date = message.created_at.strftime("%d %B %Y")

        #create embed to post in quotes channel
        embed=discord.Embed(title="Quote", color=0x80ffff)
        embed.add_field(name=msg_content, value="-- %s, [%s](%s)" % (message.author.mention, msg_date, message.jump_url), inline=False)
        embed.set_thumbnail(url=message.author.avatar_url)

        #fetch quotes channel and send embed
        quotes_channel =  self.bot.get_channel(self.quotes_channel_id)
        await quotes_channel.send(embed=embed)
        print("quotes: %s added a quote by %s." % (ctx.author, message.author))

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Quotes(bot))