import discord
from discord.ext import commands, tasks

import cogs._duel_misc as _duel_misc
import cogs._duel_challenge as _duel_challenge

import asyncio
import math
import os
import psycopg2

class Duel(commands.Cog):

    #---INIT---
    def __init__(self, bot):
        self.bot = bot

        #---CONFIGURABLE---
        self.guild_id = 253731475751436289

        self.rankings_channel = 0
        self.rankings_message = 0
        self.yes_emoji = 0
        self.no_emoji = 0
        self.duel_channels = []
        
        self.joke_emoji = 412035754613800970

        self.max_points = 2 #points needed to win
        self.wait_time = 120 #seconds to wait before asking for scores
        #self.DATABASE_URL = os.environ['DATABASE_URL'] #location of postgreSQL DB
        self.k_value = 50 #k value used in ELO calculations

        self.staff_roles = ["Secret Police"] #names of all staff roles to be mentioned/allowed use this cog
        #---•---

        self.duels_in_progress = []
        self.duels_enabled = True


        #read db url from file
        postgres_txt = open("postgres.txt", "r")
        self.DATABASE_URL = postgres_txt.read()
        postgres_txt.close()


        #db connection code
        try:
            self.database = psycopg2.connect(self.DATABASE_URL, sslmode='require')
            self.database.autocommit = True
            print("duel: Connected to database.")
        except:
            print("duel: Error connecting to the database!")

        #begin loop to keep rankings and settings up to date
        try:
            self.duel_loop.start()
            print("duel: Rankings/settings updates enabled.")
        except:
            print("duel: Error enabling rankings/settings updates.")

    def cog_unload(self):
        self.duel_loop.cancel()

    ### !--- MISC. FUNCTIONS ---! ###
    async def fetch_settings(self, guild_id):
        return await _duel_misc.fetch_settings(self, guild_id)
    async def fetch_players(self, uid=None):
        return await _duel_misc.fetch_players(self, uid)
    async def is_registered(self, member):
        return await _duel_misc.is_registered(self, member)
    async def generate_rankings_embed(self, players):
        return await _duel_misc.generate_rankings_embed(self, players)
    async def calculate_elo(self, elo1, elo2):
        return await _duel_misc.calculate_elo(self, elo1, elo2)
    async def update_points(self, uid, points, player_win):
        await _duel_misc.update_points(self, uid, points, player_win)
    async def record_duel(self, win_id, win_points, lose_id, lose_points, change):
        await _duel_misc.record_duel(self, win_id, win_points, lose_id, lose_points, change)

    #---CHECKS & COMMANDS---#
    @commands.command()
    @commands.guild_only()
    async def register(self, ctx, user: discord.Member = None):
        if user != None:
            if await self.bot.is_owner(ctx.author):
                player = user
                uid = user.id
            else:
                print("%s is not allowed to do that." % ctx.author)
                return
        else:
            player = ctx.author
            uid = ctx.message.author.id

        SQL = "INSERT INTO players (member_id, points, win, loss, streak) VALUES (%s, 1200, 0, 0, 0);"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (uid,))
            await ctx.send("You've been registered for duels, %s!" % player.mention)

        except psycopg2.Error as e:
            print("Error registering user %s:\n%s" % (player, e))
            await ctx.send("There was an error registering that user, %s. Are they already registered? If not please PM an admin." % ctx.message.author.mention)

        finally:
            cursor.close()

    @commands.command()
    @commands.guild_only()
    async def convert(self, ctx, game: str, score: int):
        sus = False

        if game.lower() == "ft2mm":
            new_score = score / 1.1
            await ctx.send("MegaMix converted score: %s" % round(new_score))

            if score > 1500000: sus = True

        elif game.lower() == "mm2ft":
            new_score = score * 1.1
            await ctx.send("Future Tone converted score: %s" % round(new_score))

            if score > 1365000: sus = True
            
        else:
            await ctx.send("Correct usage: 39!score <ft2mm> *or* <mm2ft> <score>")
        
        if sus:
            await ctx.send("That's... a suspiciously high score you got there. Might wanna check that out?")
    
    @commands.command()
    @commands.guild_only()
    async def ft2mm(self, ctx, score: int):
        await ctx.invoke(self.bot.get_command('convert'), game="ft2mm", score=score)
    @commands.command()
    @commands.guild_only()
    async def mm2ft(self, ctx, score: int):
        await ctx.invoke(self.bot.get_command('convert'), game="mm2ft", score=score)

    @commands.command()
    @commands.guild_only()
    async def rank(self, ctx):
        if not await self.is_registered(ctx.message.author):
            await ctx.send("You must be registered to view your profile, %s! Please use command 39!register in a dueling channel." % ctx.message.author.mention)
        uid = ctx.message.author.id
        #fetch all player info for embed
        SQL1 = "SELECT * FROM players WHERE member_id = %s"
        #fetch player rank sorted by ELO/points
        SQL2 = "WITH ranks as (SELECT member_id, RANK() OVER(ORDER BY points DESC) FROM players) SELECT rank FROM ranks WHERE member_id=%s"
        cursor = self.database.cursor()

        try:
            #fetch player info
            cursor.execute(SQL1, (uid,))
            player = cursor.fetchone()

            #fetch player rank
            cursor.execute(SQL2, (uid,))
            rank = cursor.fetchone()[0]

            #calculate winrate
            wins = player[3]
            losses = player[4]
            winrate = "0%" if wins == 0 else "%s%%" % str(round((wins / (wins + losses)) * 100,2)) if losses != 0 else "100%"
            streak = player[5]

            #player info embed
            embed=discord.Embed(title=str(ctx.message.author), description="Player Ranking", color=0x80ffff)
            embed.add_field(name="Rank", value=rank, inline=True)
            embed.add_field(name="ELO", value=player[2], inline=True)
            embed.add_field(name="Winrate", value=winrate, inline=False)
            embed.add_field(name="Wins", value=wins, inline=True)
            embed.add_field(name="Losses", value=losses, inline=True)
            embed.add_field(name="Winstreak", value=streak, inline=False)
            embed.set_footer(text="Use command 39!rank to view your own player info")
            embed.set_thumbnail(url=ctx.message.author.avatar_url)

            await ctx.send(embed=embed)

        finally:
            cursor.close()

    # DUEL LOGIC + CHALLENGE FUNCTIONS
    async def can_duel(self, ctx, player1, player2):
        return await _duel_challenge.can_duel(self, ctx, player1, player2)
    async def issue_challenge(self, ctx, player1, player2):
        return await _duel_challenge.issue_challenge(self, ctx, player1, player2)
    async def confirm_duel(self, ctx, player1, player2, challenge_id):
        return await _duel_challenge.confirm_duel(self, ctx, player1, player2, challenge_id)
    async def begin_round(self, ctx, player1, player2, duel_round):
        return await _duel_challenge.begin_round(self, ctx, player1, player2, duel_round)
    async def song_countdown(self, ctx):
        await _duel_challenge.song_countdown(self, ctx)
    async def confirm_scores(self, ctx, player1, player2):
        return await _duel_challenge.confirm_scores(self, ctx, player1, player2)
    async def get_winner(self, ctx, player1, player2):
        return await _duel_challenge.get_winner(self, ctx, player1, player2)
    async def confirm_winner(self, ctx, winner, loser):
        return await _duel_challenge.confirm_winner(self, ctx, winner, loser)
    async def process_duel_results(self, ctx, winner, loser, p1_score, p2_score):
        await _duel_challenge.process_duel_results(self, ctx, winner, loser, p1_score, p2_score)

    @commands.command()
    @commands.guild_only()
    async def challenge(self, ctx, player2: discord.Member):
        player1 = ctx.message.author
        
        #various checks so that duel can take place
        if not await self.can_duel(ctx, player1, player2):
            #duel checks failed
            return

        #block channel from future duels
        self.duels_in_progress.append(ctx.channel.id)

        #duel logic starts here
        challenge_id = await self.issue_challenge(ctx, player1, player2)

        if not await self.confirm_duel(ctx, player1, player2, challenge_id):
            #duel timed out or declined
            return

        #duel accepted, beginning
        await ctx.send("**Beginning Duel:** %s vs %s\n"\
            % (player1.mention, player2.mention)\
            + "First to %s point(s) wins. Priority is Perfects > Percentage > Score."\
            % self.max_points)
        
        #initialising score/round counter variables
        p1_score = 0
        p2_score = 0
        duel_round = 1

        #duel loop begins here
        while (p1_score < self.max_points and p2_score < self.max_points):
            #begin round and get song rolls, cancel if returns false
            if not await self.begin_round(ctx, player1, player2, duel_round):
                #roll timer ran out
                self.duels_in_progress.remove(ctx.channel.id)
                return

            #continue round
            await self.song_countdown(ctx)
            await asyncio.sleep(self.wait_time)

            #get players to confirm posting their scores
            if not await self.confirm_scores(ctx, player1, player2):
                #one or both players didn't confirm posting
                self.duels_in_progress.remove(ctx.channel.id)
                return
            
            #continue round
            #loop for confirming winner
            while(True):
                winner = await self.get_winner(ctx, player1, player2)
                
                if winner == 0:
                    #neither player reacted
                    #unblock channel from future duels
                    self.duels_in_progress.remove(ctx.channel.id)
                    return
            
                #break loop if winner is confirmed by the other player
                if await self.confirm_winner(ctx, player1 if winner==1 else player2, player2 if winner==1 else player1):
                    #increment winning player's score
                    if winner == 1:
                        p1_score += 1
                    else:
                        p2_score += 1

                    #break loop for confirming winner
                    break

            #send current scores and increment round counter
            await ctx.send("**Point to %s!**\n"\
                % (player1.mention if winner == 1 else player2.mention)\
                + "Current scores: %s %s - %s %s"\
                % (player1.mention, p1_score, p2_score, player2.mention))

            duel_round += 1
        
        #duel finished, announce winner and update scores/rankings
        await ctx.send("**Duel finished:** %s wins!"\
            % (player1.mention if p1_score == self.max_points else player2.mention))

        await self.process_duel_results(
                ctx,
                player1 if p1_score == self.max_points else player2,
                player2 if p1_score == self.max_points else player1,
                p1_score if p1_score == self.max_points else p2_score,
                p2_score if p1_score == self.max_points else p1_score)
        
        #unblock channel from future duels
        self.duels_in_progress.remove(ctx.channel.id)

    #---MODERATION COMMANDS---#
    async def is_mod(self, user):
        channel =  self.bot.get_channel(self.rankings_channel)
        staff_roles = [discord.utils.get(channel.guild.roles, name=role) for role in self.staff_roles]

        if any(role in staff_roles for role in user.roles):
            return True
        else:
            return False

    @commands.command()
    @commands.is_owner()
    async def unregister(self, ctx, user: discord.Member):
        member_id = user.id
        SQL = "DELETE FROM  players WHERE member_id = %s;"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (member_id,))
            await ctx.send("User unregistered.")

        except psycopg2.Error as e:
            print("Error unregistering user %s:\n%s" % (user, e))

        finally:
            cursor.close()

    @commands.command()
    @commands.is_owner()
    async def reset_user(self, ctx, user: discord.Member):
        await ctx.invoke(self.bot.get_command('unregister'), user=user)
        await ctx.invoke(self.bot.get_command('register'), user=user)
    
    @commands.command()
    @commands.is_owner()
    async def duel_results(self, ctx, duel_id):
        SQL = "SELECT * FROM duels WHERE id = %s;"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (duel_id,))
            duel = cursor.fetchone()

        except psycopg2.OperationalError as e:
            print("Error fetching duel from database:\n%s" % e)

        finally:
            cursor.close()

        win_player = self.bot.get_user(duel[1])
        win_points = duel[2]

        lose_player = self.bot.get_user(duel[3])
        lose_points = duel[4]

        change_points = "+"+str(duel[5])

        #duel info embed
        embed=discord.Embed(title="Duel Results", description="#"+str(duel_id), color=0x80ffff)
        embed.add_field(name="Winner", value=win_player, inline=True)
        embed.add_field(name="ELO", value=win_points, inline=True)
        embed.add_field(name="Change in ELO", value=change_points, inline=False)
        embed.add_field(name="Loser", value=lose_player, inline=True)
        embed.add_field(name="ELO", value=lose_points, inline=True)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def add_channel(self, ctx, channel_id: int):
        duel_settings = await self.fetch_settings(self.guild_id)
        duel_channels = duel_settings[5]

        if channel_id in duel_channels:
            await ctx.send("That channel is already enabled for dueling.")
        else:
            channel = self.bot.get_channel(channel_id)
            if channel == None:
                await ctx.send("I can't seem to find that channel.")
            else:
                duel_channels.append(channel_id)
    
                SQL = "UPDATE duel_settings SET duel_channels = %s WHERE guild_id = %s"
                cursor = self.database.cursor()

                try:
                    cursor.execute(SQL, (duel_channels, self.guild_id))
                    self.duel_channels.append(channel_id)
                    await ctx.send("Duel channel added.")

                except psycopg2.OperationalError as e:
                    print("Error adding duel channel:\n%s" % e)

                finally:
                    cursor.close()

    @commands.command()
    @commands.is_owner()
    async def remove_channel(self, ctx, channel_id: int):
        duel_settings = await self.fetch_settings(self.guild_id)
        duel_channels = duel_settings[5]

        if channel_id not in duel_channels:
            await ctx.send("That channel is not enabled for dueling.")
        else:
            duel_channels.remove(channel_id)

            SQL = "UPDATE duel_settings SET duel_channels = %s WHERE guild_id = %s"
            cursor = self.database.cursor()

            try:
                cursor.execute(SQL, (duel_channels, self.guild_id))
                self.duel_channels.remove(channel_id)
                await ctx.send("Duel channel removed.")

            except psycopg2.OperationalError as e:
                print("Error removing duel channel:\n%s" % e)

            finally:
                cursor.close()

    @commands.command()
    @commands.is_owner()
    async def duels(self, ctx):
        if self.duels_enabled:
            self.duels_enabled = False
            await ctx.send("Duels disabled, current duels will be allowed to finish.")
        else:
            self.duels_enabled = True
            await ctx.send("Duels enabled, new duels can now begin.")

    """
    @commands.command()
    @commands.guild_only()
    async def rankings(self, ctx):
        players = await self.fetch_players()

        if len(players) == 0:
            await ctx.send("There are no players registered!")

        else:
            embed = await self.generate_rankings_embed(players)
            embed.set_footer(text="Use command 39!rankings to view again")

            await ctx.send(embed=embed)
    """

    #---BACKGROUND TASKS---
    @tasks.loop(minutes=1.0)
    async def duel_loop(self):
        duel_settings = await self.fetch_settings(self.guild_id)

        self.rankings_channel = duel_settings[1]
        self.rankings_message = duel_settings[2]
        self.yes_emoji = duel_settings[3]
        self.no_emoji = duel_settings[4]
        self.duel_channels = duel_settings[5]

        players = await self.fetch_players()

        #rankings embed
        embed = await self.generate_rankings_embed(players)
        embed.set_footer(text="These rankings auto-update every minute")

        #edit existing message in #rankings channel
        channel = self.bot.get_channel(self.rankings_channel)
        message = await channel.fetch_message(self.rankings_message)
        await message.edit(content = "", embed=embed)

    @duel_loop.before_loop
    async def before_duel_loop(self):
        await self.bot.wait_until_ready()

#---SETUP---
def setup(bot):
    bot.add_cog(Duel(bot))