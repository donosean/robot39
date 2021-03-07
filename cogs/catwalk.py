import robot39
import discord
from discord.ext import commands, tasks
from datetime import datetime


class Catwalk(robot39.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.last_reminder_msg = None

        ### !--- CONFIGURABLE ---! ###
        self.catwalk_weekdays = [2] # Weekdays starting at 0 = Monday
        self.catwalk_hour = 15 # Hour of catwalk in UTC (10:00am EST)
        self.reminder_hours = [3, 12, 14] # Hours to send reminder at in UTC
        self.catwalk_channel_id = 748468857064390747 
        self.ping_role = "Fashionably Late" 

        # Find a previously posted reminder message if one exists 
        # and start the reminder checking loop
        self.last_reminder_finder.start()
        self.catwalk_loop.start()

    ### !--- METHODS ---! ###
    # Cancels currently running loops if the cog is unloaded
    def cog_unload(self):
        self.last_reminder_finder.cancel()
        self.catwalk_loop.cancel()
    
    # Deletes the message stored as an object in self.last_reminder_message
    async def delete_last_reminder(self):
        if not self.last_reminder_msg == None:
            try:
                await self.last_reminder_msg.delete()
                self.log("Deleted previous reminder message")

            except discord.Forbidden:
                self.log("Missing permissions to delete reminder message")

            except discord.NotFound:
                self.log("Message not found, possibly already deleted")
        
            except discord.HTTPException:
                self.log("Deleting the message failed")

    ### !--- TASKS ---! ###
    # Compares the current time against the hours set in __init__ and sends
    # reminder messages to the catwalk event channel at those hours
    @tasks.loop(minutes=1.0)
    async def catwalk_loop(self):
        # Only run at 0 minutes past the hour
        time = datetime.today().now()
        if not time.minute == 0:
            return

        # Only run on the same day as the catwalk event or the day before
        if not (time.weekday() in self.catwalk_weekdays
            or time.weekday()+1 in self.catwalk_weekdays):
                return

        # Get catwalk event channel and check it exists
        catwalk_channel = self.bot.get_channel(self.catwalk_channel_id)
        if not catwalk_channel:
            self.log("Channel not found, please check channel ID")
            return

        # Get role to ping with each reminder
        ping_role = discord.utils.get(catwalk_channel.guild.roles,
                                      name=self.ping_role)

        try:
            # Only run the day before the catwalk event
            if ((time.weekday() + 1) in self.catwalk_weekdays
                    and time.hour == self.catwalk_hour):
                await self.delete_last_reminder()
                self.last_reminder_msg = \
                    await catwalk_channel.send(
                        "%s! The current Catwalk will end in 24 hour(s), at"
                        " 10:00a.m. EST." % ping_role.mention)
                self.log("Reminder sent at: %s" % time)

            # Send message and ping for catwalk event ending
            elif time.hour == self.catwalk_hour:
                await self.delete_last_reminder()
                self.last_reminder_msg = None
                await catwalk_channel.send(
                        "%s! The current Catwalk has ended!"
                        % ping_role.mention)
                self.log("Catwalk finished at: %s" % time)
            
            # Send message and ping for catwalk event ending soon
            elif time.hour in self.reminder_hours:
                await self.delete_last_reminder()
                self.last_reminder_msg = \
                    await catwalk_channel.send(
                        "%s! The current Catwalk will end in %s hour(s), at"
                        " 10:00a.m. EST."
                        % (ping_role.mention,
                            (self.catwalk_hour - time.hour)))
                self.log("Reminder sent at: %s" % time)
        
        except discord.Forbidden:
            self.log("Missing permissions to send reminder message")

        except discord.HTTPException:
            self.log("Sending the reminder message failed")
            
    @catwalk_loop.before_loop
    async def before_catwalk_loop(self):
        await self.bot.wait_until_ready()

    # Checks the most recent message in the message history of the catwalk
    # event channel and stores it in self.last_reminder_message if it was
    # posted by the bot
    @tasks.loop(minutes=1.0)
    async def last_reminder_finder(self):
        # Get catwalk event channel and check it exists
        catwalk_channel = self.bot.get_channel(self.catwalk_channel_id)
        if not catwalk_channel:
            self.log("Channel not found, please check channel ID")
            return
        
        # Get most recent message in catwalk channel's message history
        # and store it if it was posted by the bot
        async for message in catwalk_channel.history(limit=1):
            if message.author == self.bot.user:
                self.last_reminder_msg = message
                self.log("Reminder message found -- %s"
                         % self.last_reminder_msg.id)

        # Print to terminal if no message was found that met the conditions
        if self.last_reminder_msg == None:
            self.log("No previous reminder message found.")
        
        # Prevent the loop from running again
        self.last_reminder_finder.stop()

    @last_reminder_finder.before_loop
    async def before_last_reminder_finder(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Catwalk(bot))