import discord
from discord.ext import commands, tasks

class Logging(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel_id = 788552632855822377
        self.log_events = {
            "ban":True,
            "delete":True,
            "edit":True
        }

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        if self.log_events["ban"]:
            #fetch ban event from audit logs
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                print("Member banned -- %s was banned by %s" % (member, entry.user)) 

                #create embed to post in logs channel
                embed=discord.Embed(title="Member Banned", color=0x80ffff)
                embed.add_field(name="Member:", value="by %s\nin %s" % member.mention, inline=False)
                embed.add_field(name="Banned by:", value=entry.user, inline=False)
                embed.set_thumbnail(url=member.avatar_url)

                #fetch logs channel and send embed
                logs_channel = self.bot.get_channel(self.logs_channel_id)
                await logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if self.log_events["edit"]:
            #print deleted message + author to log
            print("Message Edited -- %s in %s" % (before.author, before.channel.name))

            #check for empty message content due to embeds not allowing empty fields
            if len(before.content) > 0:
                msg_content = before.content
            else:
                msg_content = "No content or message contains link/embed"

            #create embed to post in logs channel
            embed=discord.Embed(title="Message Edited", color=0x80ffff)
            embed.add_field(name="Message was posted:", value="by %s\nin %s" % (before.author.mention, before.channel.mention), inline=False)
            embed.add_field(name="Mesage content:", value=msg_content, inline=False)
            embed.set_thumbnail(url=before.author.avatar_url)

            #fetch logs channel and send embed
            logs_channel = self.bot.get_channel(self.logs_channel_id)
            await logs_channel.send(embed=embed)

            #also repost any embeds contained in the deleted message
            if len(before.embeds) > 0:
                await logs_channel.send("**Deleted embeds:**")
                for embed in before.embeds:
                    await logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if self.log_events["delete"]:
            #print deleted message + author to log
            print("Message Deleted -- %s: %s" % (message.author, message.content))

            #don't repost messages deleted from logs channel
            if not message.channel.id == self.logs_channel_id:

                #check for empty message content due to embeds not allowing empty fields
                if len(message.content) > 0:
                    msg_content = message.content
                else:
                    msg_content = "No content or message contains link/embed"

                #create embed to post in logs channel
                embed=discord.Embed(title="Message Deleted", color=0x80ffff)
                embed.add_field(name="Message was posted:", value="by %s\nin %s" % (message.author.mention, message.channel.mention), inline=False)
                embed.add_field(name="Mesage content:", value=msg_content, inline=False)
                embed.set_thumbnail(url=message.author.avatar_url)

                #fetch logs channel and send embed
                logs_channel = self.bot.get_channel(self.logs_channel_id)
                await logs_channel.send(embed=embed)

                #also repost any embeds contained in the deleted message
                if len(message.embeds) > 0:
                    await logs_channel.send("**Deleted embeds:**")
                    for embed in message.embeds:
                        await logs_channel.send(embed=embed)
    
    ### !--- CHECKS & COMMANDS ---! ###
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        else:
            raise commands.NotOwner('You do not own this bot.')
    
    @commands.command()
    async def logging(self, ctx, toggle:str=None):
        if (not toggle == None) and (toggle in self.log_events):
            self.log_events[toggle] = True if False else False
            toggle_message = "logging: %s set to %s" % (toggle, self.log_events[toggle]) 
            await ctx.send(toggle_message)
            print(toggle_message)

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Logging(bot))