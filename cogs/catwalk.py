import discord
from discord.ext import commands, tasks

from datetime import datetime

class Catwalk(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot
        self.last_reminder_msg = None

        ### !--- CONFIGURABLE ---! ###
        self.catwalk_weekdays = [2, 5] #weekdays starting at 0 = Monday
        self.catwalk_hour = 15 #hour of catwalk in UTC (10:00am EST)
        self.reminder_hours = [3, 12, 14] #hours to send reminder at in UTC
        self.catwalk_channel_id = 748468857064390747 #id of catwalk channel
        self.staff_roles = ["Secret Police"] #names of all staff roles to be mentioned/allowed use this cog
        self.ping_role = "Fashionably Late" #role to be pinged with catwalk reminders

        #attempt to fetch last message sent by bot in case of restart
        try:
            self.last_reminder_finder.start()
            print("catwalk: Finding last reminder...")
        except:
            print("catwalk: Error starting finder loop.")

        #starts main loop that manages reminders/pings
        try:
            self.catwalk_loop.start()
            print("catwalk: Reminders enabled.")
        except:
            print("catwalk: Error enabling reminders.")

    def cog_unload(self):
        self.last_reminder_finder.cancel()
        self.catwalk_loop.cancel()
    
    async def delete_last_reminder(self):
        if not self.last_reminder_msg == None:
            await self.last_reminder_msg.delete()
            print("catwalk: Deleted previous reminder message.")

    ### !--- TASKS ---! ###
    @tasks.loop(minutes=1.0)
    async def catwalk_loop(self):
        time = datetime.today().now()
        
        if time.minute == 0:
            catwalk_channel = self.bot.get_channel(self.catwalk_channel_id)
            ping_role = discord.utils.get(catwalk_channel.guild.roles, name=self.ping_role)

            if time.weekday() in self.catwalk_weekdays:
                if time.hour == self.catwalk_hour:
                    await self.delete_last_reminder()
                    self.last_reminder_msg = None
                    await catwalk_channel.send("%s! The current Catwalk has ended!" % ping_role.mention)
                    print("catwalk: Catwalk finished at: %s" % time)
                
                elif time.hour in self.reminder_hours:
                    await self.delete_last_reminder()
                    self.last_reminder_msg = await catwalk_channel.send("%s! The current Catwalk will end in %s hour(s), at 10:00a.m. EST." % (ping_role.mention, (self.catwalk_hour - time.hour)))
                    print("catwalk: Reminder sent at: %s" % time)

            if (time.weekday() + 1) in self.catwalk_weekdays and time.hour == self.catwalk_hour:
                await self.delete_last_reminder()
                self.last_reminder_msg = await catwalk_channel.send("%s! The current Catwalk will end in 24 hour(s), at 10:00a.m. EST." % ping_role.mention)
                print("catwalk: Reminder sent at: %s" % time)
                
            else:
                print("catwalk: Reminder check at: %s" % time)

    @catwalk_loop.before_loop
    async def before_catwalk_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1.0)
    async def last_reminder_finder(self):
        catwalk_channel = self.bot.get_channel(self.catwalk_channel_id)
        async for message in catwalk_channel.history(limit=1):
            if message.author == self.bot.user:
                self.last_reminder_msg = message.id
                print("catwalk: Reminder message found -- %s" % self.last_reminder_msg)
        self.last_reminder_finder.stop()

    @last_reminder_finder.before_loop
    async def before_last_reminder_finder(self):
        await self.bot.wait_until_ready()

    ### !--- CHECKS & COMMANDS ---! ###
    #locks any commands of this cog to members with roles listed in self.staff_roles
    async def cog_check(self, ctx):
        if ctx.guild == None and ctx.bot.is_owner(ctx.author):
            return True
        
        catwalk_channel =  self.bot.get_channel(self.catwalk_channel_id)
        staff_roles = [discord.utils.get(catwalk_channel.guild.roles, name=role) for role in self.staff_roles]

        if any(role in staff_roles for role in ctx.author.roles):
            return True
        else:
            return False

    @commands.command()
    @commands.guild_only()
    async def catwalk(self, ctx):
        if self.catwalk_loop.is_running():
            self.catwalk_loop.cancel()
            await ctx.send("Catwalk reminders disabled.")
            print("catwalk: Reminders disabled.")
        else:
            self.catwalk_loop.start()
            await ctx.send("Catwalk reminders enabled.")
            print("catwalk: Reminders enabled.")

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Catwalk(bot))