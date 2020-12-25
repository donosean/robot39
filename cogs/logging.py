import discord
from discord.ext import commands, tasks

class Logging(commands.Cog):

    #---INIT---
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel_id = 788552632855822377

    #---EVENTS---
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        #print deleted message + author to log
        print("Message Deleted -- %s: %s" % (message.author, message.content))

        #don't repost messages deleted from logs channel
        if not message.channel.id == self.logs_channel_id:

            #check for empty message content due to embeds not allowing empty fields
            if len(message.content) > 0:
                msg_content = message.content
            else:
                msg_content = "No content or message contains link/embed"

            embed=discord.Embed(title="Message Deleted", color=0x80ffff)
            embed.add_field(name="Message was posted:", value="by %s\nin %s" % (message.author, message.channel.name), inline=False)
            embed.add_field(name="Mesage content:", value=msg_content, inline=False)
            embed.set_thumbnail(url=message.author.avatar_url)

            logs_channel = self.bot.get_channel(self.logs_channel_id)
            await logs_channel.send(embed=embed)

            if len(message.embeds) > 0:
                await logs_channel.send("**Deleted embeds:**")
                for embed in message.embeds:
                    await logs_channel.send(embed=embed)
    
    #---CHECK & COMMANDS---
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        else:
            raise commands.NotOwner('You do not own this bot.')

#---SETUP---
def setup(bot):
    bot.add_cog(Logging(bot))