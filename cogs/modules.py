import discord
from discord.ext import commands

import csv
from io import BytesIO
from PIL import Image
import psycopg2
import random

class Modules(commands.Cog):

    ### !--- INIT ---! ###
    def __init__(self, bot):
        self.bot = bot
        self.modules = {}
        self.active_drops = {}
        self.message_count = {}

        self.csv_list = [
            'etc',
            'kai',
            'len',
            'luk',
            'mei',
            'mik',
            'rin'
        ]

        #read module info from csv files
        for csv_file in self.csv_list:
            try:
                with open('modules/%s.csv' % csv_file, newline='', encoding='utf-8') as modules_file:
                    reader = csv.DictReader(modules_file)
                    self.modules[csv_file] = []
                    for row in reader:
                        self.modules[csv_file].append(row)
                print("modules: Info loaded from %s.csv for %s module(s)." % (csv_file, len(self.modules[csv_file])))
            except:
                print("modules: Error reading modules data from %s.csv." % csv_file)
        
        #read db url from file
        postgres_txt = open("postgres.txt", "r")
        self.DATABASE_URL = postgres_txt.read()
        postgres_txt.close()

        #db connection code
        try:
            self.database = psycopg2.connect(self.DATABASE_URL, sslmode='require')
            self.database.autocommit = True
            print("modules: Connected to database.")
        except:
            print("modules: Error connecting to the database!")

    #adds guild member to the player database to start tracking collection
    async def add_player(self, uid: int):
        SQL = "INSERT INTO modules (member_id, points) VALUES (%s, 0);"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (uid,))

        except psycopg2.Error as e:
            if not int(e.pgcode) == 23505:
                print("module: Error adding player info to database:\n%s" % e)

        finally:
            cursor.close()

    #fetches player info from database by given discord user id
    async def fetch_player_info(self, uid: int):
        SQL = "SELECT * FROM modules WHERE member_id = %s;"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (uid,))
            player_info = cursor.fetchone()
            return player_info

        except psycopg2.OperationalError as e:
            print("module: Error fetching player info from database:\n%s" % e)

        finally:
            cursor.close()

    #adds module card to player collection
    async def add_module(self, uid: int, module_id):
        #get player info & current module collection from db
        player = await self.fetch_player_info(uid)
        player_modules = player[3]
        
        #fixes NoneType error if the player currently has no modules
        if not type(player_modules) == list:
            player_modules = []
        
        player_modules.append(module_id)
        
        #insert player's new module collection into db
        SQL = "UPDATE modules SET collection = %s WHERE member_id = %s"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (player_modules, uid))

        except psycopg2.Error as e:
            print("modules: Error adding module %s to user:\n%s" % (module_id, e))

        finally:
            cursor.close()

    #rolls a random valid module id
    async def roll_module_id(self):
        #weighting chance to roll each set based on set size
        random_weighting = [len(self.modules[each_module_set]) for each_module_set in self.csv_list]

        #gen randon module id
        random_set = random.choices(self.csv_list, weights=random_weighting, k=1)[0]
        random_module = random.randint(1, len(self.modules[random_set]))

        #return module id
        module_id = "%s-%s" % (random_set, random_module)
        return module_id
    
    #given module_id returns file containing the module image
    async def fetch_module(self, module_id):
        #split module_id into the set name and module number
        module_set = module_id[0:3]
        module_number = int(module_id[4:])

        #define strings with path to the module and background image
        module_image = "modules/%s/%s.png" % (module_set, module_number)
        card_back = "modules/back-%s.png" % module_set

        #open the two images with Pillow
        bg_image = Image.open(card_back)
        top_image = Image.open(module_image)
        
        #paste the module image over the background in realtime
        bg_image.paste(top_image,(0, 0), top_image)
        #module_card = Image.alpha_composite(bg_image, top_image)

        #save the new image to memory
        modified_image = BytesIO()
        bg_image.save(modified_image, format='png')
        
        #open the new image as a Discord file to upload
        modified_image.seek(0)
        file = discord.File(modified_image, filename="image.png")

        return file

    #given module_id and initialised embed returns module embed to send
    async def module_embed(self, module_id, embed):
        #split module_id into the set name and module number
        module_set = module_id[0:3]
        module_number = int(module_id[4:])
        
        module = self.modules[module_set][module_number-1]
        
        #create the embed to post to Discord
        embed.add_field(name=module['ENG Name'], value=module['JP Name'], inline=False)
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text="Module id: %s" % module_id)

        return embed

    #given module_id sends the module to ctx
    @commands.command()
    async def show_module(self, ctx, module_id: str):
        #check for correct module_id format
        if not module_id[3] == '-'\
        or not (len(module_id) >=5 and len(module_id) <=7):
            return
    
        file = await self.fetch_module(module_id)
        embed = embed=discord.Embed(title="Displaying Module", color=0x80ffff)
        embed = await self.module_embed(module_id, embed)

        #finally, send the message with the new module image in an embed
        await ctx.send(file=file, embed=embed)

    #redeems currently active drop in server if given correct module id:
    @commands.command()
    async def redeem(self, ctx, module_id: str):
        #check for active drop
        if not ctx.guild.id in self.active_drops:
            await ctx.reply("There are currently no active drops in this server!")
            return
        
        #check if module_id matches current drop
        if not self.active_drops[ctx.guild.id] == module_id:
            await ctx.reply("Incorrect module id!")
            return
        
        #split module_id into the set name and module number
        module_set = module_id[0:3]
        module_number = int(module_id[4:])
        
        module = self.modules[module_set][module_number-1]
        module_name = module["ENG Name"]

        await self.add_module(ctx.author.id, module_id)
        await ctx.reply("Redeemed %s!" % module_name)
        del(self.active_drops[ctx.guild.id])

    #handles random module drops
    @commands.Cog.listener()
    async def on_message(self, message):
        #only count/track guild messages, not DMs
        if not message.guild:
            return

        #ignore messages sent by this or other bots
        if message.author.bot:
            return

        #avoids the bot overriding current active drops during redemption
        if message.content.startswith("39!redeem"):
            return

        #add player to DB in case not already registered
        await self.add_player(message.author.id)

        #only count bot owner messages while testing
        if not await self.bot.is_owner(message.author):
            return

        #start tracking current guild message count if not already
        if not message.guild.id in self.message_count:
            self.message_count[message.guild.id] = 1
            return
        
        self.message_count[message.guild.id] += 1

        """
        if self.message_count[message.guild.id] < 10:
            return
        """

        #% chance to drop module is message_count - 10
        roll = random.randint(0, 100)
        if roll <= (self.message_count[message.guild.id] + 50):
            #reset message count upon dropping module
            self.message_count[message.guild.id] = 0

            #fetch a random module
            module_id = await self.roll_module_id()
            file = await self.fetch_module(module_id)
            embed = embed=discord.Embed(title="Module Drop", color=0x80ffff)
            embed = await self.module_embed(module_id, embed)
            embed.add_field(name="** **", value="`39!redeem <module id>` to redeem.", inline=False)

            #add to active drops
            self.active_drops[message.guild.id] = module_id

            #finally, send the message with the new module image in an embed
            await message.channel.send(file=file, embed=embed)

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Modules(bot))