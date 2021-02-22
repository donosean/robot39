import discord
from discord.ext import commands


class Streaming(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 253731475751436289
        self.streaming_role = "Streaming Hearts"

    ### !--- METHODS ---! ###
    # Returns true if any of the member's activities are of type "Streaming".
    async def streaming(self, member):
        streaming = [act for act in member.activities
                     if type(act) == discord.Streaming]
        return True if streaming else False

    # Returns true if the member's activities previously included streaming,
    # but not anymore.
    async def was_streaming(self, before, after):
        return (await self.streaming(before)
                and not await self.streaming(after))

    # Returns true if the member's activities now include streaming,
    # but did not previously.
    async def is_now_streaming(self, before, after):
        return (not await self.streaming(before)
                and await self.streaming(after))

    # Adds the streaming role to the member if they didn't already have it,
    # takes it away otherwise.
    async def toggle_stream_role(self, member):
        stream_role = discord.utils.get(member.guild.roles,
                                        name=self.streaming_role)
        if not stream_role in member.roles:
            print("streaming: %s is now streaming, giving role..."
                  % member)
            await member.add_roles(stream_role)
        else:
            print("streaming: %s is no longer streaming, removing role..."
                  % member)
            await member.remove_roles(stream_role)

    ### !--- EVENTS ---! ###
    # When a member is updated, their activities are checked for any change
    # in streaming activity. Their roles are updated to reflect this.
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not after.guild.id == self.guild_id:
            return
        
        if (await self.was_streaming(before, after)
            or await self.is_now_streaming(before, after)):
                await self.toggle_stream_role(after)


def setup(bot): 
    bot.add_cog(Streaming(bot))