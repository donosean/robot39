import robot39
import discord
from discord.ext import commands, tasks
from itertools import product


class Logging(robot39.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.invites = []
        self.logs_channel_id = 788552632855822377
        self.guild_id = 253731475751436289

        self.logging_loop.start()

    ### !--- METHODS ---! ###
    # Cancels currently running loops if the cog is unloaded
    def cog_unload(self):
        self.logging_loop.cancel()

    # Caches list of currently active invites in the guild
    async def update_invites_cache(self):
        guild = await self.bot.fetch_guild(self.guild_id)
        self.invites = await guild.invites()
        self.log("Invite cache updated")
    
    # Checks if a message was posted in a guild and matches the guild ID
    # stored in self.guild_id, returning outcome as boolean
    async def is_main_guild(self, message):
        return (message.guild and message.guild.id == self.guild_id)

    ### !--- EVENTS ---! ###
    # Updates the invites cache and posts in the
    # logs channel when a new invite is created
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if not invite.guild.id == self.guild_id:
            return

        # Update invites cache and post event to the terminal
        await self.update_invites_cache()
        self.log("Invite code %s created by %s" % (invite.code, invite.inviter))

        # Create embed to post in logs channel
        embed=discord.Embed(title="Invite Created", color=0x80ffff)
        embed.add_field(name="Code:", value=invite.code, inline=False)
        embed.add_field(name="Created by:", value=invite.inviter, inline=False)
        embed.set_thumbnail(url=invite.inviter.avatar_url)

        # Fetch logs channel and send embed
        logs_channel = self.bot.get_channel(self.logs_channel_id)
        await logs_channel.send(embed=embed)

    # Updates the invites cache when an invite is deleted
    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if not invite.guild.id == self.guild_id:
            return

        await self.update_invites_cache()
        self.log("Invite code %s deleted" % invite.code)

    # Posts in the logs channel when a member is banned from the guild
    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        if not guild.id == self.guild_id:
            return

        # Checks the audit log for a ban entry involving the member
        async def find_ban_entry(guild, member):
            async for entry in guild.audit_logs(
                    action=discord.AuditLogAction.ban, limit=1):
                if entry.target == member:
                    return entry
            # Return None if the audit log entry didn't match
            return None

        # Try to find the ban entry for the member
        ban_entry = await find_ban_entry(guild, member)
        moderator = ban_entry.user.mention if ban_entry else "Unknown"

        # Print event to the terminal
        self.log("Member %s was banned by %s" % (member, moderator)) 

        # Create embed to post in logs channel
        embed=discord.Embed(title="Member Banned", color=0x80ffff)
        embed.add_field(name="Member:", value=member.mention, inline=False)
        embed.add_field(name="Banned by:", value=moderator, inline=False)
        embed.set_thumbnail(url=member.avatar_url)

        # Fetch logs channel and send embed
        logs_channel = self.bot.get_channel(self.logs_channel_id)
        await logs_channel.send(embed=embed)

    # Posts in the logs channel when a new member
    # joins the guild and updates the invites cache
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.guild.id == self.guild_id:
            return

        # Fetch current invites of guild after the member joined
        invites_after_join = await member.guild.invites()

        # Compares invites cache to invites after the member joined, looking
        # for the invite with an increased uses count since joining
        def find_used_invite(invites_before, invites_after):
            for invites in product(invites_before, invites_after):
                if (invites[0].code == invites[1].code
                        and invites[0].uses < invites[1].uses):
                    return invites[0]

            # If invite can't be found
            return None

        # Try to find which invite was used
        invite_used = find_used_invite(self.invites, invites_after_join)
        inviter = invite_used.inviter.mention if invite_used else "Unknown"
        invite_code = invite_used.code if invite_used else "Unknown"

        # Print event to the terminal
        self.log("Member %s joined via invite from %s" % (member, inviter))

        # Create embed to post in logs channel
        embed=discord.Embed(title="Member Joined", color=0x80ffff)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Member:", value=member.mention, inline=False)
        embed.add_field(name="Invited by:", value=inviter, inline=False)
        embed.add_field(name="Invite code:", value=invite_code, inline=False)

        # Fetch logs channel and send embed
        logs_channel = self.bot.get_channel(self.logs_channel_id)
        await logs_channel.send(embed=embed)

        # Update invites cache
        await self.update_invites_cache()

    # Posts in the logs channel when a member leaves/is kicked
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.guild.id == self.guild_id:
            return

        # Print event to the terminal
        self.log("Member %s left the server" % member)

        # Create embed to post in the logs channel
        embed=discord.Embed(title="Member Left", color=0x80ffff)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Member:", value=member.mention, inline=False)

        # Fetch logs channel and send embed
        logs_channel = self.bot.get_channel(self.logs_channel_id)
        await logs_channel.send(embed=embed)

    # Posts before & after content of edited messages to the logs channel
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not await self.is_main_guild(before):
            return

        # Ignore bot messages or messages with the same content
        if before.author.bot or before.content == after.content:
            return

        # Print author & channel name to the terminal
        self.log("Message edited by %s in %s"
                 % (before.author, before.channel.name))

        # Check for empty message content in before/after message
        msg_content_before = before.content if len(before.content) > 0\
            else "No content or message contains link/embed"
        msg_content_after = after.content if len(after.content) > 0\
            else "No content or message contains link/embed"

        # Create embed to post in logs channel
        embed=discord.Embed(title="Message Edited", color=0x80ffff)
        embed.set_thumbnail(url=before.author.avatar_url)
        embed.add_field(
            name="Message was posted:",
            value="by %s\nin %s"
                % (before.author.mention, before.channel.mention),
            inline=False)
        embed.add_field(
            name="Before edit:",
            value=msg_content_before,
            inline=False)
        embed.add_field(
            name="After edit:",
            value=msg_content_after,
            inline=False)
        embed.add_field(
            name="Jump to message:",
            value="[[Click Here]](%s)"
                % before.jump_url,
            inline=False)

        # Fetch logs channel and send embed
        logs_channel = self.bot.get_channel(self.logs_channel_id)
        await logs_channel.send(embed=embed)

    # Posts content of deleted messages to the logs channel
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not await self.is_main_guild(message):
            return

        # Print author & channel name to the terminal
        self.log("Message from %s was deleted in %s"
                 % (message.author, message.channel))

        # Don't repost messages deleted from the logs channel
        if message.channel.id == self.logs_channel_id:
            return

        # Check for empty message content
        msg_content = message.content if len(message.content) > 0\
            else "No content or message contains link/embed"

        # Create embed to post in logs channel
        embed=discord.Embed(title="Message Deleted", color=0x80ffff)
        embed.set_thumbnail(url=message.author.avatar_url)
        embed.add_field(
            name="Message was posted:",
            value="by %s\nin %s"
                % (message.author.mention, message.channel.mention),
            inline=False)
        embed.add_field(
            name="Mesage content:",
            value=msg_content,
            inline=False)

        # Fetch logs channel and send embed
        logs_channel = self.bot.get_channel(self.logs_channel_id)
        await logs_channel.send(embed=embed)

        # Post any embeds contained in the deleted message
        if len(message.embeds) > 0:
            await logs_channel.send("*Message contained these embeds:*")
            for embed in message.embeds:
                await logs_channel.send(embed=embed)

    ### !--- TASKS ---! ###
    # Updates the invite cache once upon loading the cog, then doesn't run again
    @tasks.loop(minutes=1.0)
    async def logging_loop(self):
        await self.update_invites_cache()
        self.logging_loop.stop()

    @logging_loop.before_loop
    async def before_logging_loop(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Logging(bot))