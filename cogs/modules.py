import discord
from discord.ext import commands

import csv
from datetime import date
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
        self.player_ids = []
        self.drop_channel_id = 253731475751436289

        self.csv_list = [
            'etc',
            'kai',
            'len',
            'luk',
            'mei',
            'mik',
            'rin'
        ]

        self.set_names = {
            'etc': 'Others',
            'kai': 'Kaito',
            'len': 'Len',
            'luk': 'Luka',
            'mei': 'Meiko',
            'mik': 'Miku',
            'rin': 'Rin'
        }

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
        
        #cache all current user ids from db
        self.update_player_ids()

    #caches list of currently registered discord user ids to reduce db operations
    def update_player_ids(self):
        SQL = "SELECT member_id from modules;"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL)
            sql_output = cursor.fetchall()
            player_ids = [id[0] for id in sql_output]

            self.player_ids = player_ids

        except psycopg2.Error as e:
                print("module: Error fetching member IDs from database:\n%s" % e)

        finally:
            cursor.close()

    #adds guild member to the player database to start tracking collection
    async def add_player(self, uid: int):
        #do nothing if user id is already known to be registered
        if uid in self.player_ids:
            return

        SQL = "INSERT INTO modules (member_id, points) VALUES (%s, 0);"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (uid,))
            self.player_ids.append(uid)

        except psycopg2.Error as e:
            if not int(e.pgcode) == 23505:
                print("module: Error adding player info to database:\n%s" % e)

        finally:
            cursor.close()
    
    #marks a player's daily as redeemed in db
    async def mark_daily(self, uid: int, date: str):
        #do nothing if uid is not registered
        if not uid in self.player_ids:
            return

        SQL = "UPDATE modules SET last_daily = %s WHERE member_id = %s;"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL, (date, uid))

        except psycopg2.Error as e:
                print("module: Error marking player daily in database:\n%s" % e)

        finally:
            cursor.close()

    #fetches player info from database by given discord user id
    async def fetch_player_info(self, uid: int):
        #return None if user id is known to not be registered
        if not uid in self.player_ids:
            return None

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
    async def add_module(self, uid: int, module_id, add_vp: int = 0):
        #registers user if user id is known to not have been
        if not uid in self.player_ids:
            await self.add_player(uid)

        #get player info & current module collection from db
        player = await self.fetch_player_info(uid)
        player_modules = player[3]
        
        #fixes NoneType error if the player currently has no modules
        if not type(player_modules) == list:
            player_modules = []
        
        player_modules.append(module_id)
        
        #insert player's new module collection into db
        if add_vp == 0:
            SQL = "UPDATE modules SET collection = %s WHERE member_id = %s"
        else:
            SQL = "UPDATE modules SET collection = %s, points = points + %s WHERE member_id = %s"

        cursor = self.database.cursor()

        try:
            if add_vp == 0:
                cursor.execute(SQL, (player_modules, uid))
            else:
                cursor.execute(SQL, (player_modules, add_vp, uid))

        except psycopg2.Error as e:
            print("modules: Error adding module %s to user:\n%s" % (module_id, e))

        finally:
            cursor.close()

    #remvoes module card from player collection
    async def remove_module(self, uid: int, module_id):
        #registers user if user id is known to not have been
        if not uid in self.player_ids:
            await self.add_player(uid)

        #get player info & current module collection from db
        player = await self.fetch_player_info(uid)
        player_modules = player[3]
        
        #fixes NoneType error if the player currently has no modules
        if not type(player_modules) == list:
            return
        
        #return if module isn't in player collection
        if not module_id in player_modules:
            return

        #remove the module from player collection
        player_modules.remove(module_id)
        
        #insert player's new module collection into db
        SQL = "UPDATE modules SET collection = %s WHERE member_id = %s"
        cursor = self.database.cursor()
        try:
            cursor.execute(SQL, (player_modules, uid))

        except psycopg2.Error as e:
            print("modules: Error removing module %s from user:\n%s" % (module_id, e))

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
    @commands.is_owner()
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

    #like show_module() but only works if module is in collection
    @commands.command()
    async def view(self, ctx, module_id: str):
        #register user if not already
        if not ctx.author.id in self.player_ids:
            await self.add_player(ctx.author.id)
        
        #check for correct module_id format
        if not module_id[3] == '-'\
        or not (len(module_id) >=5 and len(module_id) <=7):
            return

        #fetch player_info and create list of collection
        player_info = await self.fetch_player_info(ctx.author.id)
        player_collection = player_info[3]
    
        #check for module id in player collection
        if not module_id in player_collection:
            await ctx.reply("You do not own that module, sorry!")
            return

        #continue if found, creating module file and embed to send
        file = await self.fetch_module(module_id)
        embed = embed=discord.Embed(title="Displaying Module", color=0x80ffff)
        embed = await self.module_embed(module_id, embed)

        #finally, send the message with the new module image in an embed
        await ctx.send(file=file, embed=embed)

    #redeems currently active drop in server if given correct module id:
    @commands.command()
    async def redeem(self, ctx, module_id: str):
        #register user if not already
        if not ctx.author.id in self.player_ids:
            await self.add_player(ctx.author.id)

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

        await self.add_module(ctx.author.id, module_id, add_vp = 100)
        await ctx.reply("Redeemed %s! You gained 100 VP." % module_name)
        del(self.active_drops[ctx.guild.id])

    #gives module from module id to mentioned player if module is owned
    @commands.command()
    async def give_module(self, ctx, module_id: str, receiving_user: discord.Member):
        #register user if not already
        if not ctx.author.id in self.player_ids:
            await self.add_player(ctx.author.id)
            return

        #check for correct module_id format
        if not module_id[3] == '-'\
        or not (len(module_id) >=5 and len(module_id) <=7):
            return

        #fetch player_info and create list of collection
        player_info = await self.fetch_player_info(ctx.author.id)
        player_collection = player_info[3]
    
        #check for module id in player collection or empty collection
        if (not player_collection) or (not module_id in player_collection):
            await ctx.reply("You do not own that module, sorry!")
            return

        if receiving_user.bot:
            await ctx.reply("The bot appreciates the gesture, but politely declines.")
            return

        #register receiving user if not already
        if not receiving_user.id in self.player_ids:
            await self.add_player(receiving_user.id)

        await self.remove_module(ctx.author.id, module_id)
        await self.add_module(receiving_user.id, module_id)
        
        #split module_id into the set name and module number
        module_set = module_id[0:3]
        module_number = int(module_id[4:])
        
        module = self.modules[module_set][module_number-1]

        await ctx.reply("You gave %s -- %s to %s." % (module_id, module['ENG Name'], receiving_user.mention))
    
    #gives random module and medium amount of VP, usable once a day per user
    @commands.command()
    async def daily(self, ctx):
        #register user if not already
        if not ctx.author.id in self.player_ids:
            await self.add_player(ctx.author.id)

        #fetch player info and todays day of the month as int
        player_info = await self.fetch_player_info(ctx.author.id)  
        today = str(date.today())

        #only continue if daily isn't marked as redeemed
        if today == player_info[4]:
            await ctx.reply("You've already redeemed your daily for today!")
            return

    	#roll random module and add to collection with daily VP bonus
        module_id = await self.roll_module_id()
        await self.add_module(ctx.author.id, module_id, add_vp=500)

        #prepare embed to show to user
        file = await self.fetch_module(module_id)
        embed = embed=discord.Embed(title="Daily Redeemed", color=0x80ffff)
        embed = await self.module_embed(module_id, embed)
        embed.add_field(name="** **", value="You gained 500 VP.")

        #send the embed to the user and mark their daily as completed
        await ctx.send(file=file, embed=embed)        
        await self.mark_daily(ctx.author.id, today)

    #displays member profile stats including collection & VP
    @commands.command()
    async def modules(self, ctx):
        #register player if not already
        if not ctx.author.id in self.player_ids:
            await self.add_player(ctx.author.id)

        #fetch player info incl. modules collection
        player_info = await self.fetch_player_info(ctx.author.id)

        #convert module collection from list to set to remove duplicates
        collection_set = {}
        if player_info[3]:
            collection_set = set(player_info[3])

        #get a count of how many modules from each set the player has
        collection_counts = {}
        for module_set in self.csv_list:
            collection_counts[module_set] = len([module_id for module_id in collection_set if module_id.startswith(module_set)])

        #create embed for player info
        embed = embed=discord.Embed(title="Module Collection Stats", color=0x80ffff)
        embed.set_thumbnail(url=ctx.message.author.avatar_url)
        embed.set_footer(text="Use command 39!collection to view a full list")
        embed.add_field(name="User:", value=ctx.author.mention, inline=True)
        embed.add_field(name="VP:", value=player_info[2], inline=True)

        embed.add_field(name="Collection:", value="** **", inline=False)

        #add field to the embed for each module set
        for module_set in self.csv_list:
            embed.add_field(name="%s:" % self.set_names[module_set], value="%s/%s" % (collection_counts[module_set], len(self.modules[module_set])), inline=True)
        
        #count total available modules and % completion
        total_modules = sum(len(module_set) for module_set in self.modules.values())
        collection_percentage = 0 if len(collection_set) == 0\
            else round((len(collection_set) / total_modules) * 100, 2)

        #add overall completion & VP to embed
        embed.add_field(name="Overall:", value="**%s/%s (%s%%)**" % (len(collection_set), total_modules, collection_percentage), inline=False)

        #finally, send the embed
        await ctx.send(embed=embed)

    #displays detailed list of module collection
    @commands.command()
    async def collection(self, ctx, page_number: int = 1):
        #register player if not already
        if not ctx.author.id in self.player_ids:
            await self.add_player(ctx.author.id)

        player_info = await self.fetch_player_info(ctx.author.id)
        player_collection = player_info[3]

        #do nothing if collection is empty
        if not player_collection:
            return
        
        player_collection.sort()

        #split player collection into pages with 20 cards max
        pages = [player_collection[i:i + 20] for i in range(0, len(player_collection), 20)]  

        #avoids index out of range error
        if page_number > len(pages) or page_number < 1:
            page_number = 1

        #embed to display card collection
        embed = embed=discord.Embed(title="Module Collection List", color=0x80ffff)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text="Viewing page %s of %s\nAdd a page number after 39!collection to view other pages" % (page_number, len(pages)))

        #loop through selected page and form string of module ids + names
        module_list = ""
        for module_id in pages[page_number-1]:
            #split module id into set and number
            module_set = module_id[0:3]
            module_number = int(module_id[4:])

            #fetch module info from memory
            module = self.modules[module_set][module_number-1]

            #append module id + name to string that will be part of embed
            module_list += "• %s -- %s\n" % (module_id, module['ENG Name'])
        
        embed.add_field(name="Modules:", value=module_list, inline=False)

        #finally, send list embed
        await ctx.send(embed=embed)

    #handles random module drops
    @commands.Cog.listener()
    async def on_message(self, message):
        #only count/track guild messages, not DMs
        if not message.guild:
            return

        #ignore messages sent by this or other bots
        if message.author.bot:
            return

        #don't count commands towards message count
        if message.content.startswith("39!"):
            return

        #start tracking current guild message count if not already
        if not message.guild.id in self.message_count:
            self.message_count[message.guild.id] = 1
            return
        
        #increment message counter
        self.message_count[message.guild.id] += 1
 
        #at least 20 messages needed before rolling for a drop chance
        if self.message_count[message.guild.id] < 20:
            return

        #% chance to drop module is message_count - 15
        #so once 20 messages have been sent drop chance = 5%
        #increasing by 1% per message sent
        roll = random.randint(0, 100)
        if roll <= (self.message_count[message.guild.id] - 15):
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
            drop_channel = await self.bot.get_channel(self.drop_channel_id)
            await drop_channel.send(file=file, embed=embed)

### !--- SETUP ---! ###
def setup(bot):
    bot.add_cog(Modules(bot))