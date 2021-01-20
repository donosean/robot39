import discord
from discord.ext import commands


class NoMimic(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Listens for member updates and checks for nickname changes. If the new
    # nickname matches that of the bot, it is cleared.
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Ignore bot member updates and unchanged nicknames
        if after.bot or before.nick == after.nick:
            return

        # Compare new nickname to bot's current nickname,
        # clearing it if they match
        if after.nick == after.guild.me.nick:
            try:
                member = after.guild.get_member(after.id)
                await member.edit(nick=None)
                print("nomimic: Caught matching nickname,"
                      "cleared for user %s" % member)
            
            except discord.Forbidden:
                print("nomimic: Missing permissions to clear nickname for %s"
                      % after)
            
            except discord.HTTPException:
                print("nomimic: Nickname clear operation failed for %s" % after)


def setup(bot):
    bot.add_cog(NoMimic(bot))