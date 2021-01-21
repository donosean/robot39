import discord
from discord.ext import commands

import json
from typing import Union


class AutoRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.settings = {}
        self.settings_file = "data/autorole.json"

        self.load_settings()

    ### !--- METHODS ---! ###
    # Loads the settings the self.settings_file;
    # Only called when cog is loaded
    def load_settings(self):
        try:
            settings_json = open(self.settings_file, "r")
            settings_string = settings_json.read()

            # Only decode the JSON if it isn't empty
            if settings_string:
                try:
                    self.settings = json.loads(settings_string)

                # Cog will not load if it can't be decoded
                except json.JSONDecodeError:
                    print("autorole: Error decoding contents of %s, "
                          "cannot load cog" % self.settings_file[5:])
                    raise commands.ExtensionFailed

            print("autorole: Loaded settings for %s server(s)"
                  % len(self.settings))

        except OSError:
            # Create settings file if it's missing
            print("autorole: Error opening %s for reading, "
                  "this file will be created" % self.settings_file[5:])
            try:
                settings_json = open(self.settings_file, "w")

            # Cog will not load if it can't find/create settings file
            except OSError:
                print("autorole: Error creating %s, cannot load cog."
                      % self.settings_file[5:])
                raise commands.ExtensionFailed

        settings_json.close()

    # Saves the settings currently in self.settings to self.settings_file
    async def save_settings(self):
        # Attempt to open settings JSON for writing
        try:
            settings_json = open(self.settings_file, "w")

        # Return False if file can't be opened or created
        except OSError:
            print("autorole: Error saving settings to %s!"
                  % self.settings_file[5:])
            return False

        # Encode the settings to JSON format and save the file
        settings_string = json.dumps(self.settings, indent=4)
        settings_json.write(settings_string)
        settings_json.close()
        return True

    # Returns discord.Role object of the currently set role
    # for a particular guild
    async def get_autorole(self, guild) -> discord.Role:
        # Check if settings exist for the current guild, return if not
        guild_id_str = str(guild.id)
        if not guild_id_str in self.settings:
            return None

        # Fetch the role from the role ID stored in settings
        role_id = self.settings[guild_id_str]
        role = guild.get_role(role_id)

        return role

    # Sends the same text to both the context channel and the terminal
    async def say(self, ctx, text):
        try:
            await ctx.reply(text)
        except discord.Forbidden:
            print("autorole: Missing permissions to reply.")

        print("autorole: %s" % text)

    ### !--- EVENTS ---! ###
    # Adds the configured role to new members
    # on a per guild basis if one is set
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Fetch configured autorole for the current guild, return if none
        role = await self.get_autorole(member.guild)
        if not role:
            return

        # Add the role to the new member
        try:
            await member.add_roles(role)
            print("autorole: Role '%s' added to %s." % (role.name, member))

        except discord.Forbidden:
            print("autorole: Missing permissions to add role '%s' to %s."
                  % (role.name, member))

        except discord.HTTPException:
            print("autorole: Failed to add role '%s' to %s."
                  % (role.name, member))

    ### !--- CHECKS & COMMANDS ---! ###
    # Restricts all commands in this cog to specific checks
    async def cog_check(self, ctx):
        # Allow bot owner and server admins
        if (await ctx.bot.is_owner(ctx.author)
                or ctx.author.guild_permissions.administrator):
            return True

        raise commands.NotOwner(
            'autorole: %s does not own this bot.' % ctx.author)

    # Displays the role currently set for the server, if one is configured
    @commands.command()
    @commands.guild_only()
    async def autorole(self, ctx):
        # Check if settings exist for the current guild, return if not
        role = await self.get_autorole(ctx.guild)
        if not role:
            await self.say(
                ctx, "This server is either not configured for autorole, "
                     "or the previously set role could not be found.")
            return

        await self.say(
            ctx, "The autorole configured for this server is: %s" % role.name)

    # Sets the autorole for the server to the one given, if it can be found
    @commands.command()
    @commands.guild_only()
    async def autorole_set(self, ctx, role: Union[discord.Role, str]):
        # Fetch the role if the name is passed as a string instead of a mention
        if not type(role) == discord.Role:
            role = discord.utils.get(ctx.guild.roles, name=role)

        # Only continue upon confirming the role exists in current guild
        if not role in ctx.guild.roles:
            await self.say(ctx, "There was an error finding that role.")
            return

        # Add the role to the settings for the current guild
        self.settings[str(ctx.guild.id)] = role.id
        if await self.save_settings():
            await self.say(ctx, "The autorole for this server "
                                "has been set to: %s" % role.name)
        else:
            await self.say(ctx, "The role was found, but there was "
                                "an error saving it to the settings.")

    # Deletes the autorole settings for the current server, if they exist
    @commands.command()
    @commands.guild_only()
    async def autorole_unset(self, ctx):
        # Check if settings exist for the current guild, return if not
        role = await self.get_autorole(ctx.guild)
        if not role:
            await self.say(
                ctx, "This server is either not configured for autorole,"
                     "or the previously set role could not be found.")
            return

        # Delete the settings for the current guild and save
        del self.settings[str(ctx.guild.id)]
        if await self.save_settings():
            await self.say(ctx, "The autorole for this server has been unset.")
        else:
            await self.say(ctx, "There was an error removing the "
                                "settings for this server.")


def setup(bot):
    bot.add_cog(AutoRole(bot))