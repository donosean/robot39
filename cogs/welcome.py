import discord
from discord.ext import commands

class Welcome(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot

        #message sent on new member join
        self.welcome_message =\
        "Welcome to Channel 39, %s! To see the rest of the server you'll need to answer three questions:\n\
        1. What Project Diva games do you have?\n\
        2. How long have you been playing Project Diva?\n\
        3. How did you find out about this server?\n\
        Please type 'done' when you're finished."

        #message sent on new member answer
        self.final_message =\
        "Thanks for answering! Your answers will be reviewed by one of our staff shortly. Please read the rules above while you wait.\n%s"

        ### !--- CONFIGURABLE ---! ###
        self.welcome_channel_id = 413887244407930900 #get this by right clicking on your #welcome channel and clicking "Copy ID"
        self.rules_message_id = 785146157218791424 #rules message to not delete on channel purge
        self.staff_roles = ["Secret Police", "Assistant"] #names of all staff roles to be mentioned/allowed use this cog
        self.new_member_role = "Tier 0" #name of role to grant new members

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_member_join(self, member):
        print("welcome: %s joined the server." % member)
        welcome_channel =  self.bot.get_channel(self.welcome_channel_id)

        if not member.bot:
            #send welcome message
            welcome_channel =  self.bot.get_channel(self.welcome_channel_id)
            await welcome_channel.send(self.welcome_message % member.mention)
            print("welcome: Welcome message sent.")

            #check for new member typing confirmation message in welcome channel
            def check(message):
                return message.author == member\
                    and message.channel == welcome_channel\
                    and message.content.lower().startswith("done")
            
            await self.bot.wait_for('message', check=check) #await above check

            #list of staff mentions as string
            staff_mentions = ""
            for role in self.staff_roles:
                staff_role = discord.utils.get(welcome_channel.guild.roles, name=role)
                staff_mentions += staff_role.mention

            await welcome_channel.send(self.final_message % staff_mentions) #send final message to new member & ping staff
            print("welcome: %s has answered the welcome questions, staff pinged." % member)
        else:
            await welcome_channel.send("Hi there, %s! Do you want to be my bot friend?")

    ### !--- CHECKS & COMMANDS ---! ###
    #locks any commands of this cog to members with roles listed in self.staff_roles
    async def cog_check(self, ctx):
        welcome_channel =  self.bot.get_channel(self.welcome_channel_id)
        staff_roles = [discord.utils.get(welcome_channel.guild.roles, name=role) for role in self.staff_roles]

        if any(role in staff_roles for role in ctx.author.roles) and ctx.channel == welcome_channel:
            return True
        else:
            return False

    @commands.command()
    @commands.guild_only()
    async def allow(self, ctx, member: discord.Member):
        if not any(role.name.startswith("Tier") for role in member.roles): #only executes if member doesn't have a Tier role
            #fetch Tier 0 role
            welcome_channel =  self.bot.get_channel(self.welcome_channel_id)
            new_member_role = discord.utils.get(welcome_channel.guild.roles, name=self.new_member_role)

            await member.add_roles(new_member_role) #add Tier 0 role to member
            await ctx.send("Welcome to the server, %s!" % member.name)

            print("welcome: %s has been allowed into the server by %s." % (member, ctx.author))

    @commands.command()
    @commands.guild_only()
    async def clear(self, ctx):
        #fetch channel + message objects
        welcome_channel =  self.bot.get_channel(self.welcome_channel_id)
        rules_message = await welcome_channel.fetch_message(self.rules_message_id)
        
        print("welcome: Purging welcome...")
        await welcome_channel.purge(after=rules_message) #purge everything except rules message
        print("welcome: Purge complete.")

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Welcome(bot))