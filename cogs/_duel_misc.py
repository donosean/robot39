import discord

import math
import psycopg2

async def fetch_settings(self, guild_id):
    SQL = "SELECT * FROM duel_settings WHERE guild_id = %s;"
    cursor = self.database.cursor()

    try:
        cursor.execute(SQL, (guild_id,))
        duel_settings = cursor.fetchone()

    except psycopg2.OperationalError as e:
        print("Error fetching duel settings from database:\n%s" % e)

    finally:
        cursor.close()
        return duel_settings

async def fetch_players(self, uid=None):
    SQL = "SELECT * FROM players"
    if uid == None: SQL += " ORDER BY points DESC;"
    else: SQL += " WHERE member_id = %s;"

    cursor = self.database.cursor()

    try:
        if uid == None:
            cursor.execute(SQL)
            players = cursor.fetchall()
        else:
            cursor.execute(SQL, (uid,))
            players = cursor.fetchone()
        return players

    except psycopg2.OperationalError as e:
        print("Error fetching player(s) from database:\n%s" % e)

    finally:
        cursor.close()

async def is_registered(self, member):
    uid = member.id
    players = await self.fetch_players()

    if len(players) == 0:
        return False

    else:
        registered_uids = [player[1] for player in players]
        return uid in registered_uids

async def generate_rankings_embed(self, players):
    embed=discord.Embed(color=0x80ffff)
    
    if len(players) == 0:
        print("duel: No players registered.")
    
    else:
        #list comprehensions to prepare strings for rankings embed
        ranks = "\n".join([str(i) for i in range(1, len(players)+1)])
        names = "\n".join([str(await self.bot.fetch_user(player[1])) for player in players])
        points = "\n".join([str(player[2]) for player in players])

        embed.set_author(name="Player Rankings")
        embed.add_field(name="Rank", value=ranks, inline=True)
        embed.add_field(name="Player", value=names, inline=True)
        embed.add_field(name="ELO", value=points, inline=True)

    return embed

async def calculate_elo(self, elo1, elo2):
    power = (elo2 - elo1) / 400
    p1_chance = round(1 / (1 + math.pow(10, power)), 2)
    win_points = int(round((1 - p1_chance) * self.k_value, 0))

    return win_points

async def update_points(self, uid, points, player_win):
    SQL = "UPDATE players SET points = %s"\
        + (", win = win + 1, streak = streak + 1" if player_win else ", loss = loss + 1, streak = 0")\
        +" WHERE member_id = %s;"
    cursor = self.database.cursor()

    try:
        cursor.execute(SQL, (points, uid))

    except psycopg2.OperationalError as e:
        print("Error updating player points:\n%s" % e)

    finally:
        cursor.close()

async def record_duel(self, win_id, win_points, lose_id, lose_points, change):
    SQL = "INSERT INTO duels"\
        + " (win_id, win_points, lose_id, lose_points, change)"\
        + " VALUES (%s, %s, %s, %s, %s);"
    cursor = self.database.cursor()

    try:
        cursor.execute(SQL,\
            (win_id, win_points, lose_id, lose_points, change))

    except psycopg2.Error as e:
        print("Error recording duel:\n%s" % e)

    finally:
        cursor.close()