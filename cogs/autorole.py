import discord
from discord.ext import commands

import json
from typing import Union

class AutoRole(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot

        #settings will be loaded into this dict
        self.settings = {}

        #file to load settings from
        self.settings_file = "data/autorole.json"

        self.load_settings()
    
    ### !--- METHODS ---! ###
    #loads the settings for this cog from self.settings_file, only called when cog is loaded
    def load_settings(self):
        #load cog settings from file
        try:
            settings_json = open(self.settings_file, "r")
            settings_string = settings_json.read()

            #only decide the json if not empty
            if settings_string:
                try:
                    self.settings = json.loads(settings_string)
                
                #cog will not load if decoding json contents fails
                except json.JSONDecodeError:
                    print("autorole: Error decoding contents of %s, cannot load cog." % self.settings_file[5:])
                    raise commands.ExtensionFailed
        
        except OSError:
            #create file if missing
            print("autorole: Error opening %s for reading, this file will be created." % self.settings_file[5:])
            try:
                settings_json = open(self.settings_file, "w")
            
            #cog will not load if unable to find or create settings json
            except OSError:
                print("autorole: Error creating %s, cannot load cog." % self.settings_file[5:])
                raise commands.ExtensionFailed

        settings_json.close()
    
    #saves the settings currently in self.settings to self.settings_file
    async def save_settings(self):
        #attempt to open settings json for writing
        try:
            settings_json = open(self.settings_file, "w")
        
        #return false if file can't be opened or created
        except OSError:
            print("autorole: Error saving settings to %s!" % self.settings_file[5:])
            return False
        
        #finally encode the settings to json format and save the file
        settings_string = json.dumps(self.settings, indent=4)
        settings_json.write(settings_string)
        settings_json.close()
        return True

    #returns a discord.Role object if one is set for the guild passed to it, False otherwise or None if role is not found
    async def get_autorole(self, guild):
        #check if settings exist for the current guild, return if not
        guild_id_str = str(guild.id)
        if not guild_id_str in self.settings:
            #await self.say(ctx, "This server is not currently configured for autorole.")
            return False
        
        #fetch the role from the role id stored in settings
        role_id = self.settings[guild_id_str]
        role = guild.get_role(role_id)

        return role

    #sends the same text to both context and the terminal
    async def say(self, ctx, text):
        try:
            await ctx.reply(text)
        except discord.Forbidden:
            print("autorole: Missing permissions to reply.")
        
        print("autorole: %s" % text)

    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_member_join(self, member):
        #fetch configured autorole for the current guild
        role = await self.get_autorole(member.guild)

        #if it exists, attempt to add it to the new member
        if role:
            try:
                await member.add_roles(role)
                print("autorole: Role '%s' added to %s." % (role.name, member))

            except discord.Forbidden:
                print("autorole: Missing permissions to add role '%s' to %s." % (role.name, member))

            except discord.HTTPException:
                print("autorole: Failed to add role '%s' to %s." % (role.name, member))
        
    ### !--- CHECKS & COMMANDS ---! ###
    async def cog_check(self, ctx):
        #all commands are only accessible to the owner of the bot
        if await ctx.bot.is_owner(ctx.author):
            return True

        #or users with admin permissions in their guild
        elif ctx.author.guild_permissions.administrator:
            return True

        #and no one else
        else:
            raise commands.NotOwner('autorole: %s does not own this bot.' % ctx.author)
    
    #replies to the user with the currently set role for the server, if one is configured
    @commands.command()
    @commands.guild_only()
    async def autorole(self, ctx):
        #check if settings exist for the current guild, return if not
        role = await self.get_autorole(ctx.guild)

        #if above returned either False or None
        if not role:
            await self.say(ctx, "This server is either not configured for autorole, or the previously set role could not be found.")
            return
        
        #respond to user
        await self.say(ctx, "The autorole configured for this server is: %s" % role.name)

    #sets the autorole for the server to the one given, if it can be found
    @commands.command()
    @commands.guild_only()
    async def autorole_set(self, ctx, role: Union[discord.Role, str]):
        #fetch the role if the name is passed as a string instead of a mention
        if not type(role) == discord.Role:
            role = discord.utils.get(ctx.guild.roles, name=role)
        
        #only continue upon confirming role exists in current guild
        if not role in ctx.guild.roles:
            await self.say(ctx, "There was an error finding that role.")
            return
        
        #add the role to the settings for the current guild
        self.settings[str(ctx.guild.id)] = role.id
        if await self.save_settings():
            await self.say(ctx, "The autorole for this server has been set to: %s" % role.name)
        else:
            await self.say(ctx, "The role was found, but there was an error saving it to the settings.")
    
    #deletes the autorole settings for the current server, if they exist
    @commands.command()
    @commands.guild_only()
    async def autorole_unset(self, ctx):
        #check if settings exist for the current guild, return if not
        role = await self.get_autorole(ctx.guild)

        #check if the saved role id still exists as a role in the current guild, return if not
        if not role:
            await self.say(ctx, "This server is either not configured for autorole, or the previously set role could not be found.")
            return
        
        #delete the settings for the current guild and save
        del self.settings[str(ctx.guild.id)]
        if await self.save_settings():
            await self.say(ctx, "The autorole for this server has been unset.")
        else:
            await self.say(ctx, "There was an error removing the settings for this server.")

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(AutoRole(bot))