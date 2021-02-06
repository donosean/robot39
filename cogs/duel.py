import discord
from discord.ext import commands, tasks

import cogs._duel_misc as _duel_misc
import cogs._duel_challenge as _duel_challenge

import asyncio
import ast
import csv
import psycopg2
import secrets

class Duel(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot

        ### !--- CONFIGURABLE ---! ###
        self.guild_id = 253731475751436289

        self.rankings_channel = 0
        self.rankings_message = 0
        self.dlc_channel = 0
        self.yes_emoji = 0
        self.no_emoji = 0
        self.duel_channels = []
        self.songs = []
        
        self.dlc_msgs = [
            796151572396507157,
            796151578192248852
        ]
        self.joke_emoji = 412035754613800970

        self.wait_time = 120 #seconds to wait before asking for scores
        self.k_value = 50 #k value used in ELO calculations

        self.staff_roles = ["Secret Police"] #names of all staff roles to be mentioned/allowed use this cog
        
        self.dlc_packs = {
            'FT FS': 'FT Future Sound',
            'FT CT': 'FT Colorful Tone',
            'FT DLC1': 'FT DLC Pack 1',
            'FT DLC2': 'FT DLC Pack 2',
            'FT DLC3': 'FT DLC Pack 3',
            'FT DX': 'FT DX Pack',
            'FT MM': 'FT MegaMix Pack 1',
            'FT MM2': 'FT MegaMix Pack 2',
            'MegaMix': 'MegaMix Base Game',
            'MM DLC1': 'MM DLC Pack 1',
            'MM DLC2': 'MM DLC Pack 2',
            'MM DLC3': 'MM DLC Pack 3',
            'MM DLC4': 'MM DLC Pack 4',
            'MM DLC5': 'MM DLC Pack 5',
            'MM DLC6': 'MM DLC Pack 6',
            'MM DLC7': 'MM DLC Pack 7',
            'MM DLC8': 'MM DLC Pack 8',
            'MM DLC9': 'MM DLC Pack 9',
            'MM DLC10': 'MM DLC Pack 10',
            'MM DLC11': 'MM DLC Pack 11',
            'MM Theme': 'MM Theme Song Pack',
            'MM Sega': 'MM SEGA Song Pack'
        }
        ### !--- • ---! ###

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
        
        #read song info from csv
        try:
            with open('data/duel/song_data.csv', newline='', encoding='utf-8') as songs_file:
                reader = csv.DictReader(songs_file)
                for row in reader:
                    self.songs.append(row)
            print("duel: Info loaded for %s song(s)." % len(self.songs))
        except:
            print("duel: Error reading song data from song_data.csv.")
        
        #read dictionary of DLC packs + emoji equivalents to dict
        try:
            dlc_dict_txt = open('data/duel/dlc_dict.txt', 'r', encoding='utf-8')
            dlc_dict_content = dlc_dict_txt.read()
            self.dlc_dict = ast.literal_eval(dlc_dict_content)
            dlc_dict_txt.close()
            print("duel: DLC dictionary read from dlc_dict.txt.")
        except:
            print("duel: Error reading DLC dictionary from dlc_dict.txt.")

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
    async def calculate_elo(self, elo1, elo2, multiplier):
        return await _duel_misc.calculate_elo(self, elo1, elo2, multiplier)
    async def update_points(self, uid, points, player_win):
        await _duel_misc.update_points(self, uid, points, player_win)
    async def record_duel(self, win_id, win_points, lose_id, lose_points, change):
        await _duel_misc.record_duel(self, win_id, win_points, lose_id, lose_points, change)
    async def update_dlc(self, user, action, dlc):
        await _duel_misc.update_dlc(self, user, action, dlc)

    ### !--- CHECKS & COMMANDS ---! ###
    @commands.command()
    @commands.guild_only()
    async def register(self, ctx, user: discord.Member = None):
        if user != None:
            if await self.bot.is_owner(ctx.author):
                player = user
                uid = user.id
            else:
                print("duel: %s is not allowed to do that." % ctx.author)
                return
        else:
            player = ctx.author
            uid = ctx.message.author.id

        SQL = "INSERT INTO players (member_id, points, win, loss, streak) VALUES (%s, 1200, 0, 0, 0);"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (uid,))
            await ctx.send("You've been registered for duels, %s! Please set your owned song packs in the duel DLC channel." % player.mention)

        except psycopg2.Error as e:
            print("duel: Error registering user %s:\n%s" % (player, e))
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

    @commands.command()
    @commands.guild_only()
    async def my_dlc(self, ctx):
        if not await self.is_registered(ctx.message.author):
            await ctx.send("You must be registered to view your DLC, %s! Please use command 39!register in a dueling channel." % ctx.message.author.mention)
        uid = ctx.message.author.id
        #fetch all player info for embed
        SQL1 = "SELECT dlc FROM players WHERE member_id = %s"
        cursor = self.database.cursor()

        try:
            #fetch player dlc
            cursor.execute(SQL1, (uid,))
            dlc_list = (cursor.fetchone())[0]

            #only continue if player actually has DLC set
            if not dlc_list:
                await ctx.send("You haven't selected any DLC yet, %s! Please go to the duel DLC channel.")

            dlc_owned = [self.dlc_packs[dlc] for dlc in dlc_list]
            dlc_for_embed = '\n'.join(sorted(dlc_owned))

            #player info embed
            embed=discord.Embed(title=str(ctx.message.author), description="Player Games & DLC", color=0x80ffff)
            embed.add_field(name="Owned:", value=dlc_for_embed, inline=True)
            embed.set_footer(text="Use command 39!my_dlc to view your own DLC")
            embed.set_thumbnail(url=ctx.message.author.avatar_url)

            await ctx.send(embed=embed)

        finally:
            cursor.close()
    
    @commands.command()
    @commands.guild_only()
    async def roll(self, ctx, player2: discord.Member):
        player1 = ctx.message.author

        if not await self.is_registered(player1):
            await ctx.send("You must be registered to duel to use this feature, %s!" % player1)
            return
        
        if not await self.is_registered(player2):
            await ctx.send("That user isn't registered to duel, %s!" % player1)
            return
        
        shared_songs_list = await self.get_shared_songs(player1, player2)
        if (len(shared_songs_list) == 0) or (type(shared_songs_list) == None):
            await ctx.send("It seems neither of you have any songs in common to duel with! Please check your settings in the duel DLC channel.")
            self.duels_in_progress.remove(ctx.channel.id)
            print("duel: Error, no songs in common between %s and %s." % (player1, player2))
            return

        random_song = secrets.choice(shared_songs_list)
        await ctx.send("Rolled a random song that %s and %s have in common...\nYour random song roll is: **%s**" % (player1, player2, random_song))
        print("duel: Rolled random song for %s and %s" % (player1, player2))

    ### !--- DUEL LOGIC & CHALLENGE FUNCTIONS ---! ###
    async def can_duel(self, ctx, player1, player2):
        return await _duel_challenge.can_duel(self, ctx, player1, player2)
    async def get_shared_songs(self, player1, player2):
        return await _duel_challenge.get_shared_songs(self, player1, player2)
    async def get_max_points(self, ctx, duel_type):
        return await _duel_challenge.get_max_points(self, ctx, duel_type)
    async def issue_challenge(self, ctx, player1, player2, duel_type):
        return await _duel_challenge.issue_challenge(self, ctx, player1, player2, duel_type)
    async def confirm_duel(self, ctx, player1, player2, challenge_id):
        return await _duel_challenge.confirm_duel(self, ctx, player1, player2, challenge_id)
    async def begin_round(self, ctx, player1, player2, duel_round, shared_songs_list):
        return await _duel_challenge.begin_round(self, ctx, player1, player2, duel_round, shared_songs_list)
    async def song_countdown(self, ctx):
        await _duel_challenge.song_countdown(self, ctx)
    async def confirm_scores(self, ctx, player1, player2):
        return await _duel_challenge.confirm_scores(self, ctx, player1, player2)
    async def get_winner(self, ctx, player1, player2):
        return await _duel_challenge.get_winner(self, ctx, player1, player2)
    async def confirm_winner(self, ctx, winner, loser):
        return await _duel_challenge.confirm_winner(self, ctx, winner, loser)
    async def process_duel_results(self, ctx, winner, loser, duel_max_points):
        await _duel_challenge.process_duel_results(self, ctx, winner, loser, duel_max_points)

    @commands.command()
    @commands.guild_only()
    async def challenge(self, ctx, player2: discord.Member, duel_type: str = "bo3"):
        player1 = ctx.message.author

        #various checks so that duel can take place
        if not await self.can_duel(ctx, player1, player2):
            #duel checks failed
            return

        #block channel from future duels
        self.duels_in_progress.append(ctx.channel.id)

        #duel logic starts here
        duel_max_points = await self.get_max_points(ctx, duel_type)
        if not duel_max_points:
            await ctx.send("That's not a valid duel option, %s! Your choices are bo3, bo5, or bo9 for a best of 3, 5, or 9 rounds respectively.\n" % player1.mention\
                +"Leave this option out to default to a best of 3 duel.")
            self.duels_in_progress.remove(ctx.channel.id)
            return

        challenge_id = await self.issue_challenge(ctx, player1, player2, duel_type)
        print("duel: %s issued a %s challenge to %s" % (player1, duel_type.lower(), player2))

        if not await self.confirm_duel(ctx, player1, player2, challenge_id):
            #duel timed out or declined
            return

        #duel accepted, beginning
        #get shared songs between both players and end duel if list is empty
        shared_songs_list = await self.get_shared_songs(player1, player2)
        if (len(shared_songs_list) == 0) or (type(shared_songs_list) == None):
            await ctx.send("It seems neither of you have any songs in common to duel with! Please check your settings in the duel DLC channel.")
            self.duels_in_progress.remove(ctx.channel.id)
            print("duel: Error, no songs in common between %s and %s." % (player1, player2))
            return

        print("duel: %s accepted the challenge from %s" % (player2, player1))
        await ctx.send("**Beginning Duel:** %s vs %s\n"\
            % (player1.mention, player2.mention)\
            + "First to %s point(s) wins. Priority is Perfects > Percentage > Score."\
            % duel_max_points)
        
        #initialising score/round counter variables
        p1_score = 0
        p2_score = 0
        duel_round = 1

        #duel loop begins here
        while (p1_score < duel_max_points and p2_score < duel_max_points):
            #begin round and get song rolls, cancel if returns false
            if not await self.begin_round(ctx, player1, player2, duel_round, shared_songs_list):
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
            % (player1.mention if p1_score == duel_max_points else player2.mention))

        await self.process_duel_results(
                ctx,
                player1 if p1_score == duel_max_points else player2,
                player2 if p1_score == duel_max_points else player1,
                duel_max_points
                )
        
        #unblock channel from future duels
        self.duels_in_progress.remove(ctx.channel.id)

    ### !--- MODERATION ---! ###
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
            print("duel: Error unregistering user %s:\n%s" % (user, e))

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
            print("duel: Error fetching duel from database:\n%s" % e)
            duel = None

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
                    print("duel: Error adding duel channel:\n%s" % e)

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
                print("duel: Error removing duel channel:\n%s" % e)

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
    
    @commands.command()
    @commands.is_owner()
    async def force_win(self, ctx, winner: discord.Member, loser: discord.Member, mode: str = None):
        max_points = 3 if mode == "bo5"\
            else 5 if mode == "bo9"\
            else 2

        await self.process_duel_results(ctx, winner, loser, max_points)
        print("duel: Victory forced in favor of %s vs %s." % (winner, loser))

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
    ### !--- EVENTS ---! ###
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if (not payload.message_id in self.dlc_msgs):
            return

        member = self.bot.get_user(payload.user_id)
        if not await self.is_registered(member):
            channel =  self.bot.get_channel(self.dlc_channel)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
            print("duel: %s is not registered, DLC reaction removed." % member)
            return

        emoji = str(payload.emoji)
        if emoji in self.dlc_dict:
            await self.update_dlc(payload.user_id, 'add', self.dlc_dict[emoji])

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.message_id in self.dlc_msgs:
            return

        member = self.bot.get_user(payload.user_id)
        if not await self.is_registered(member):
            return

        emoji = str(payload.emoji)
        if emoji in self.dlc_dict:
            await self.update_dlc(payload.user_id, 'remove', self.dlc_dict[emoji])
    
    ### !--- TASKS ---! ###
    @tasks.loop(minutes=1.0)
    async def duel_loop(self):
        duel_settings = await self.fetch_settings(self.guild_id)

        self.rankings_channel = duel_settings[1]
        self.rankings_message = duel_settings[2]
        self.yes_emoji = duel_settings[3]
        self.no_emoji = duel_settings[4]
        self.duel_channels = duel_settings[5]
        self.dlc_channel = duel_settings[6]

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

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Duel(bot))