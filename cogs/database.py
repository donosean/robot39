import discord
from discord.ext import commands

import psycopg2

POSTGRES_FILE = 'postgres.txt'


class Database(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Read database URL from file
        try:
            postgres_txt = open(POSTGRES_FILE, "r")

        except OSError:
            print(bot.FILE_MISSING_ERROR % POSTGRES_FILE)
            raise commands.ExtensionFailed

        postgres_txt = open(POSTGRES_FILE, "r")
        self.DATABASE_URL = postgres_txt.read()
        postgres_txt.close()

        # Connect to database
        try:
            self.connection = psycopg2.connect(self.DATABASE_URL,
                                             sslmode='require')
            self.connection.autocommit = True
            self.log("Connected to database")

        except psycopg2.Error:
            self.log("Error connecting to the database!")
            raise commands.ExtensionFailed
    
    def log(self, text):
        print("%s: %s" % (self.qualified_name, text))


def setup(bot):
    bot.add_cog(Database(bot))