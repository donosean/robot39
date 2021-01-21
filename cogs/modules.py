import discord
from discord.ext import commands

import asyncio
import csv
from datetime import date
from enum import Enum
from io import BytesIO
from iteration_utilities import duplicates
from natsort import natsorted
from PIL import Image
import psycopg2
import random
from typing import Union


class DatabaseAction(Enum):
    add_player = "INSERT INTO modules (member_id, points) VALUES (%s, 0);"
    mark_daily = "UPDATE modules SET last_daily = %s WHERE member_id = %s;"
    fetch_user = "SELECT * FROM modules WHERE member_id = %s;"
    add_vp = "UPDATE modules SET points = points + %s WHERE member_id = %s"
    remove_vp = "UPDATE modules SET points = points - %s WHERE member_id = %s"
    update_collection = "UPDATE modules SET collection = %s "\
                        "WHERE member_id = %s"

    def __init__(self, SQL):
        self.SQL = SQL


class Modules(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.modules_dict = {}
        self.active_drops = {}
        self.message_count = {}
        self.player_ids = []

        self.drop_channel_id = 799282021725110282
        
        self.min_msgs_before_drop = 20
        self.initial_drop_percent = 5

        # List of CSV files to load module info from at load
        self.csv_list = [
            'etc',
            'kai',
            'len',
            'luk',
            'mei',
            'mik',
            'rin'
        ]

        # Full names of each module set
        self.set_names = {
            'etc': 'Others',
            'kai': 'Kaito',
            'len': 'Len',
            'luk': 'Luka',
            'mei': 'Meiko',
            'mik': 'Miku',
            'rin': 'Rin'
        }

        # Read module info from CSV files
        for csv_file in self.csv_list:
            try:
                # Open each csv file with a csv.DictReader and append each row
                # to a list
                with open('data/modules/%s.csv'
                          % csv_file, newline='', encoding='utf-8')\
                          as modules_file:
                    reader = csv.DictReader(modules_file)
                    self.modules_dict[csv_file] = []
                    for row in reader:
                        self.modules_dict[csv_file].append(row)
                    
                # Print how many entries are loaded from each CSV file
                print("modules: Info loaded from %s.csv for %s module(s)"
                      % (csv_file, len(self.modules_dict[csv_file])))

            except Exception as e:
                print("modules: Error reading modules data from %s.csv\n%s"
                      % (csv_file, e))
        
        # Read database URL from file
        postgres_txt = open("postgres.txt", "r")
        self.DATABASE_URL = postgres_txt.read()
        postgres_txt.close()

        # Connect to database
        try:
            self.database = psycopg2.connect(self.DATABASE_URL,
                                             sslmode='require')
            self.database.autocommit = True
            print("modules: Connected to database")

        except:
            print("modules: Error connecting to the database!")
        
        # Cache all current user IDs from database
        self.update_player_ids()

    ### !--- METHODS ---! ###
    # Caches list of currently registered Discord user IDs in database
    def update_player_ids(self):
        SQL = "SELECT member_id from modules;"
        cursor = self.database.cursor()

        try:
            cursor.execute(SQL)
            sql_output = cursor.fetchall()

            # The database returns a list of lists, only
            # the first element in each list is desired
            player_ids = [id[0] for id in sql_output]
            self.player_ids = player_ids

        except psycopg2.Error as e:
                print("module: Error fetching member IDs from database:\n%s"
                      % e)

        finally:
            cursor.close()

    # Splits a module_id into its set and number components
    # For module_id 'mik-123': 'mik' is the set, '123' is the number
    async def split_module_id(self, module_id: str) -> dict:
        module_set = module_id[0:3]
        module_number = int(module_id[4:])

        module = {
            'set': module_set,
            'number': module_number
        }
        return module

    # Fetches the info for a given module_id including
    # its set, number, English name and Japanese name
    async def fetch_module_info(self, module_id: str) -> dict:
        module = await self.split_module_id(module_id)

        # Get other module info from info that was read
        # from the CSV files and add to the dictionary
        module_info = self.modules_dict[module['set']][module['number']-1]
        module['ENG Name'] = module_info['ENG Name']
        module['JP Name'] = module_info['JP Name']

        return module

    # Checks if a module_id is valid and that the module exists
    async def is_valid_module_id(self, module_id: str) -> bool:
        # The module_id must have a hyphen in position 4
        # and be between 5 and 7 characters total length
        if (not module_id[3] == '-'
                or not (len(module_id) >=5 and len(module_id) <=7)):
            return False

        module = await self.split_module_id(module_id)

        # Check if module set exists and module number exists within that set
        if (module['set'] in self.modules_dict
                and module['number']-1 \
                <= len (self.modules_dict[module['set']])):
            return True
        
        # Not a valid module_id
        return False

    # Executes all database actions used by other methods in this cog,
    # using SQL statements defined in the DatabaseAction enum
    async def database_action(self, action: DatabaseAction, uid: int,
                              value: Union[str, list, int] = None):
        # Prepare data to be used in query
        data = (value, uid)
        if action == DatabaseAction.add_player\
                or action == DatabaseAction.fetch_user:
            data = (uid,)

        # Execute database action
        cursor = self.database.cursor()
        try:
            cursor.execute(action.SQL, data)

            # Add the Discord user ID to cache if a new player was registered
            if action == DatabaseAction.add_player:
                self.player_ids.append(uid)
            
            # Return the fetched info if database was queried for player info
            elif action == DatabaseAction.fetch_user:
                return cursor.fetchone()

        except psycopg2.Error as e:
                print("module: Error executing database action '%s':\n%s"
                      % (action, e))

        finally:
            cursor.close()

    # Adds guild member to the player database to start tracking collection
    async def add_player_by_uid(self, uid: int):
        await self.database_action(DatabaseAction.add_player, uid)
    
    # Marks a player's daily as redeemed in the database
    async def mark_daily_as_redeemed(self, uid: int, date: str):
        # Do nothing if uid is not registered
        if not uid in self.player_ids:
            return

        await self.database_action(DatabaseAction.mark_daily, uid, date)

    # Fetches player info from database by given Discord user ID
    async def fetch_player_info_by_uid(self, uid: int):
        # Return None if uid is known to not be registered (not cached)
        if not uid in self.player_ids:
            return None

        return await self.database_action(DatabaseAction.fetch_user, uid)

    # Adds or removes a module (module_id) from a player (uid)
    async def manage_player_collection(self, action: str,
                                       uid: int, module_id: str):
        # Register user if uid is not in the cache
        if not uid in self.player_ids:
            await self.add_player_by_uid(uid)

            # Do nothing as the newly registered player has no modules to remove
            if action == "remove_module":
                return

        # Get player info and current module collection
        player = await self.fetch_player_info_by_uid(uid)
        player_modules = player[3]
        
        # Return if player collection is already empty, or initialise empty list
        # for adding a module to an empty collection
        if not type(player_modules) == list:
            if action == "remove_module": return
            else: player_modules = []
        
        # Add module_id to the player's collection
        if action == "add_module":
            player_modules.append(module_id)

        # Or remove module_id from the player's collection if it exists
        elif action == "remove_module":
            if not module_id in player_modules: return
            else: player_modules.remove(module_id)

        # Commit updated player collection to database
        await self.database_action(DatabaseAction.update_collection,
                                   uid, player_modules)

    # Adds a module (module_id) to a player (uid)
    async def add_module_to_player(self, uid: int, module_id: str):
        await self.manage_player_collection(uid, module_id, action="add_module")

        user = self.bot.get_user(uid)
        print("modules: Added %s to %s" % (module_id, user))

    # Removes a module (module_id) from a player (uid)
    async def remove_module_from_player(self, uid: int, module_id: str):
        await self.manage_player_collection(uid, module_id,
                                            action="remove_module")

        user = self.bot.get_user(uid)
        print("modules: Removed %s from %s" % (module_id, user))
    
    # Adds VP amount to player's current total
    async def add_vp_to_player(self, uid: int, amount: int):
        await self.database_action(DatabaseAction.add_vp, uid, amount)

        user = self.bot.get_user(uid)
        print("modules: Added %s VP to %s" % (amount, user))

    # Removes VP amount from player's current total
    async def remove_vp_from_player(self, uid: int, amount: int):
        await self.database_action(DatabaseAction.remove_vp, uid, amount)

        user = self.bot.get_user(uid)
        print("modules: Removed %s VP from %s" % (amount, user))

    # Rolls a random valid module_id
    async def roll_module_id(self, module_set: str = None) -> str:
        # Roll random set if not specified, weighting each set by
        # size to give each module an even chance of being rolled
        if not module_set:
            set_weights = [len(self.modules_dict[each_module_set])
                           for each_module_set in self.csv_list]
            module_set = random.choices(
                           self.csv_list, weights=set_weights, k=1)[0]
        
        # Roll random valid ID from the chosen set
        random_module = random.randint(1, len(self.modules_dict[module_set]))
        module_id = "%s-%s" % (module_set, random_module)
        return module_id
    
    # Prepares an image of a module (module_id) to be posted to Discord
    async def get_module_file(self, module_id: str) -> discord.File:
        module = await self.split_module_id(module_id)

        # File paths to module images and module background
        module_image = "data/modules/%s/%s.png"\
                       % (module['set'], module['number'])
        card_back = "data/modules/back-%s.png" % module['set']

        # Open the two images with Pillow and paste
        # the module over the background image
        try:
            top_image = Image.open(module_image)
            bg_image = Image.open(card_back)
        
        except FileNotFoundError:
            print("modules: Image file(s) not found for module %s" % module)
            return

        bg_image.paste(top_image,(0, 0), top_image)

        # Save the new image to memory and pass it
        # to a Discord File object to return
        modified_image = BytesIO()
        bg_image.save(modified_image, format='png')
        modified_image.seek(0)
        file = discord.File(modified_image, filename="image.png")

        return file

    # Prepares embed containing module image and information to post to Discord
    async def fill_module_embed(self, module_id: str,
                                embed: discord.Embed) -> discord.Embed:
        module = await self.fetch_module_info(module_id)

        embed.set_image(url="attachment://image.png")
        embed.set_footer(text="Module ID: %s" % module_id)
        embed.add_field(name=module['ENG Name'], value=module['JP Name'],
                inline=False)

        return embed
    
    async def display_player_collection(self, ctx, page_number: int = 1,
                                        duplicates_only: bool = False):
        # Register new player if Discord user ID is not in the cache,
        # then return as they have no collection
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)
            return

        player_info = await self.fetch_player_info_by_uid(ctx.author.id)
        player_collection = player_info[3]

        # Do nothing if collection is empty
        if not player_collection:
            return
        
        embed_title = "Module Collection List"
        command_name = "39!collection"

        # If displaying only duplicates, filter the player
        # collection and check that there are any
        if duplicates_only:
            player_collection = list(duplicates(player_collection))
            if not player_collection:
                return
            
            # Change embed text to match command used
            embed_title = "Module Duplicates List"
            command_name = "39!duplicates"

        # Sort player collection and split into pages of 20
        player_collection = natsorted(player_collection)
        pages = [player_collection[i:i + 20]
                 for i in range(0, len(player_collection), 20)]  

        # Default to page 1 if page doesn't exist
        if page_number > len(pages) or page_number < 1:
            page_number = 1

        # Create player collection embed
        embed = embed=discord.Embed(title=embed_title, color=0x80ffff)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(
            text="Viewing page %s of %s\n"
                 "Add a page number after %s to view other pages"
                 % (page_number, len(pages), command_name))

        # Loop through selected page and append module_id + English name to
        # string for use in embed
        module_list = ""
        for module_id in pages[page_number-1]:
            module = await self.fetch_module_info(module_id)
            module_list += "• %s -- %s\n" % (module_id, module['ENG Name'])
        
        embed.add_field(name="Modules:", value=module_list, inline=False)
        await ctx.send(embed=embed)

    ### !--- COMMANDS ---! ###
    # Adds module (module_id) to player (uid)
    @commands.command()
    @commands.is_owner()
    async def add_module(self, ctx, module_id: str, uid: int):
        await self.add_module_to_player(uid, module_id)

    # Removes module (module_id) from player (uid)
    @commands.command()
    @commands.is_owner()
    async def remove_module(self, ctx, module_id: str, uid: int):
        await self.remove_module_from_player(uid, module_id)
    
    # Adds VP amount (amount) to player (uid)
    @commands.command()
    @commands.is_owner()
    async def add_vp(self, ctx, amount: int, uid: int):
        await self.add_vp_to_player(uid, amount)
    
    # Removes VP amount (amount) from player (uid)
    @commands.command()
    @commands.is_owner()
    async def remove_vp(self, ctx, amount: int, uid: int):
        await self.remove_vp_from_player(uid, amount)

    # Displays module (module_id) in context channel
    @commands.command()
    @commands.is_owner()
    async def show_module(self, ctx, module_id: str):
        # Check for valid module_id
        if not await self.is_valid_module_id(module_id):
            return
    
        # Get module image and embed
        file = await self.get_module_file(module_id)
        embed = embed=discord.Embed(title="Displaying Module", color=0x80ffff)
        embed = await self.fill_module_embed(module_id, embed)

        await ctx.send(file=file, embed=embed)

    # Like show_module() but only works if module is in player collection
    @commands.command(name='view', aliases=['show'])
    async def view(self, ctx, module_id: str):
        # Register and return if the user isn't registered already
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)
            return

        # Check for valid module_id        
        if not await self.is_valid_module_id(module_id):
            return

        # Fetch player_info and create list of collection
        player_info = await self.fetch_player_info_by_uid(ctx.author.id)
        player_collection = player_info[3]
    
        # Check module_id exists in the player's collection
        if not module_id in player_collection:
            await ctx.reply("You do not own that module, sorry!")
            return

        # Get the image and embed for the module
        file = await self.get_module_file(module_id)
        embed = embed=discord.Embed(title="Displaying Module", color=0x80ffff)
        embed = await self.fill_module_embed(module_id, embed)
        await ctx.send(file=file, embed=embed)

    # Redeems a currently active drop in the server
    # if the correct module ID is typed
    @commands.command()
    async def redeem(self, ctx, module_id: str):
        # Register new players
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)

        # Check for active drop and matching module_id
        if not (ctx.guild.id in self.active_drops
                and self.active_drops[ctx.guild.id] == module_id):
            return

        # Remove the drop and add the module to player collection
        del(self.active_drops[ctx.guild.id])
        await self.add_module_to_player(ctx.author.id, module_id)
        await self.add_vp_to_player(ctx.author.id, amount=100)
        
        # Send reply message
        module = await self.fetch_module_info(module_id)
        module_name = module["ENG Name"]
        await ctx.reply("Redeemed %s! You gained 100 VP." % module_name)
        print("modules: %s redeemed by %s" % (module_id, ctx.author))

    # Gives module (module_id) to mentioned player if module is owned by author
    @commands.command()
    async def give_module(self, ctx, module_id: str,
                          receiving_user: discord.Member):
        # Register and return if the author is a new player
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)
            return

        if not await self.is_valid_module_id(module_id):
            return

        # Fetch player info and module collection
        player_info = await self.fetch_player_info_by_uid(ctx.author.id)
        player_collection = player_info[3]
    
        # Check that collection isn't empty and module_id is owned
        if (not player_collection) or (not module_id in player_collection):
            await ctx.reply("You do not own that module, sorry!")
            return

        # You can't give something to yourself
        if receiving_user == ctx.author:
            await ctx.reply(
                "You took the module card out of your left pocket,"
                " and moved it into your right. Good job.")
            return

        # You can't give something to a bot account
        if receiving_user.bot:
            await ctx.reply(
                "The bot appreciates the gesture, but politely declines.")
            return

        # Register receiving_user if they're a new player
        if not receiving_user.id in self.player_ids:
            await self.add_player_by_uid(receiving_user.id)

        # Swap the module between players
        await self.remove_module_from_player(ctx.author.id, module_id)
        await self.add_module_to_player(receiving_user.id, module_id)
        
        # Send reply
        module = await self.fetch_module_info(module_id)
        module_name = module["ENG Name"]
        await ctx.reply(
            "You gave %s -- %s to %s."
            % (module_id, module_name, receiving_user.mention))
        print("modules: %s given to %s by %s"
              % (module_id, ctx.author, receiving_user))

    # Gives VP (amount) to mentioned player if author has enough
    @commands.command()
    async def give_vp(self, ctx, amount: int, receiving_user: discord.Member):
        # Register and return if author isn't registered already
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)
            return

        # Do nothing if invalid VP amount specified
        if amount < 1:
            return

        # Fetch author's player info and current VP amount
        player_info = await self.fetch_player_info_by_uid(ctx.author.id)
        player_points = player_info[2]
    
        # Check author has enough VP to give
        if amount > player_points:
            await ctx.reply("You don't have enough VP to do that, sorry!")
            return

        # You can't give VP to yourself
        if receiving_user == ctx.author:
            await ctx.reply("Congratulations, you paid yourself.")
            return

        # You can't give VP to a bot account
        if receiving_user.bot:
            await ctx.reply(
                "The bot appreciates the gesture, but politely declines.")
            return

        # Register the receiving user if they're a new player
        if not receiving_user.id in self.player_ids:
            await self.add_player_by_uid(receiving_user.id)

        # Swap the VP between players and reply
        await self.remove_vp_from_player(ctx.author.id, amount)
        await self.add_vp_to_player(receiving_user.id, amount)
        await ctx.reply(
            "You gave %s VP to %s." % (amount, receiving_user.mention))
        print(
            "modules: %s VP given to %s by %s"
            % (amount, receiving_user, ctx.author))
    
    # Gives a random module and 500 VP to the author, usable once per day
    @commands.command()
    async def daily(self, ctx):
        # Register author if they're a new player
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)

        # Fetch author's player info and today's date for checking daily status
        player_info = await self.fetch_player_info_by_uid(ctx.author.id)  
        today = str(date.today())

        # Check if daily was already redeemed today
        if today == player_info[4]:
            await ctx.reply("You've already redeemed your daily for today!")
            return

    	# Add random module & 500 VP to author
        module_id = await self.roll_module_id()
        await self.add_module_to_player(ctx.author.id, module_id)
        await self.add_vp_to_player(ctx.author.id, amount=500)

        # Get image and embed for the new module
        file = await self.get_module_file(module_id)
        embed = embed=discord.Embed(title="Daily Redeemed", color=0x80ffff)
        embed = await self.fill_module_embed(module_id, embed)
        embed.add_field(name="** **", value="You gained 500 VP.")

        # Mark the daily as redeemed and reply to author
        await self.mark_daily_as_redeemed(ctx.author.id, today)
        await ctx.send(file=file, embed=embed)        
        print("modules: Daily redeemed by %s" % ctx.author)

    # Player can buy a random module for 1000 VP or specify a set for 1500 VP
    @commands.command(name='purchase', aliases=['buy'])
    async def purchase(self, ctx, module_set: str = None):
        # Register author if they're a new player
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)

        # Fetch player info and current VP
        player_info = await self.fetch_player_info_by_uid(ctx.author.id)
        player_points = player_info[2]

        # Check the module set is valid if specified
        if module_set and not module_set in self.modules_dict:
            await ctx.reply("That is not a valid module set!")
            return
        
        # Check the player can afford the option chosen
        vp_cost = 1500 if module_set else 1000
        if player_points < vp_cost:
            await ctx.reply(
                "You must have at least %s VP to perform that action."
                % vp_cost)
            return

    	# Add random module to author's collection and remove VP cost
        module_id = await self.roll_module_id(module_set=module_set)
        await self.add_module_to_player(ctx.author.id, module_id)
        await self.remove_vp_from_player(ctx.author.id, amount=vp_cost)

        # Get module image & embed and send reply
        file = await self.get_module_file(module_id)
        embed = embed=discord.Embed(title="Rolled Module", color=0x80ffff)
        embed = await self.fill_module_embed(module_id, embed)
        embed.add_field(name="** **", value="You spent %s VP." % vp_cost)
        await ctx.send(file=file, embed=embed)        
        print("modules: %s rolled a module" % ctx.author)

    # Displays player collection stats including VP and completion percentage
    @commands.command()
    async def modules(self, ctx):
        # Register author if they're a new player
        if not ctx.author.id in self.player_ids:
            await self.add_player_by_uid(ctx.author.id)

        # Fetch player info from database
        player_info = await self.fetch_player_info_by_uid(ctx.author.id)

        # Convert player collection to set to remove duplicates
        collection_set = {}
        if player_info[3]:
            collection_set = set(player_info[3])

        # Count number of modules player has in each set
        collection_counts = {}
        for module_set in self.csv_list:
            collection_counts[module_set] =\
                len([module_id for module_id in collection_set
                    if module_id.startswith(module_set)])

        # Create embed containing player stats
        embed = embed=discord.Embed(title="Module Collection Stats",
                                    color=0x80ffff)
        embed.set_thumbnail(url=ctx.message.author.avatar_url)
        embed.set_footer(text="Use command 39!collection to view a full list")
        embed.add_field(name="User:", value=ctx.author.mention, inline=True)
        embed.add_field(name="VP:", value=player_info[2], inline=True)

        embed.add_field(name="Collection:", value="** **", inline=False)

        # Add an embed field for each module set
        for module_set in self.csv_list:
            embed.add_field(
                name="%s:" % self.set_names[module_set],
                value="%s/%s" 
                    % (collection_counts[module_set],
                       len(self.modules_dict[module_set])),
                inline=True)
        
        # Count total number of modules that can be collected
        # and calculate completion percentage
        total_modules =\
            sum(len(module_set) for module_set in self.modules_dict.values())
        collection_percentage =\
            0 if len(collection_set) == 0\
                else round((len(collection_set) / total_modules) * 100, 2)

        # Add overall completion and current VP to the embed and send it
        embed.add_field(
            name="Overall:",
            value="**%s/%s (%s%%)**"
                % (len(collection_set), total_modules, collection_percentage),
            inline=False)
        await ctx.send(embed=embed)

    # Displayed detailed list of player's module collection
    @commands.command(name='collection', aliases=['col'])
    async def collection(self, ctx, page_number: int = 1):
        await self.display_player_collection(ctx=ctx, page_number=page_number)

    # Same as above but only displays duplicate modules
    @commands.command(name='duplicates', aliases=['dupes', 'spares'])
    async def duplicates(self, ctx, page_number: int = 1):
        await self.display_player_collection(ctx=ctx, page_number=page_number,
                                             duplicates_only=True)

    ### !--- EVENTS ---! ###
    #handles random module drops
    @commands.Cog.listener()
    async def on_message(self, message):
        # Don't track DMs, bot messages, or commands
        if (not message.guild
                or message.author.bot
                or message.content.startswith("39!")):
            return

        # Increment guild message counter
        self.message_count[message.guild.id] =\
            1 if not message.guild.id in self.message_count\
                else self.message_count[message.guild.id] + 1
 
        # Check if guild message counter has reached the minimum needed
        if self.message_count[message.guild.id] < self.min_msgs_before_drop:
            return

        # Roll random number up to 100 and check if it's high enough to drop
        roll = random.randint(0, 100)
        if roll <= (self.message_count[message.guild.id]
                    - (self.min_msgs_before_drop - self.initial_drop_percent)):
            # Invoke typing until message containing drop is sent
            drop_channel = self.bot.get_channel(self.drop_channel_id)
            async with drop_channel.typing():
                # Reset message count and add random module to active drops
                self.message_count[message.guild.id] = 0
                module_id = await self.roll_module_id()
                self.active_drops[message.guild.id] = module_id

                # Get module image and create embed
                file = await self.get_module_file(module_id)
                embed = embed=discord.Embed(title="Module Drop", color=0x80ffff)
                embed = await self.fill_module_embed(module_id, embed)
                embed.add_field(
                    name="** **",
                    value="`39!redeem <module id>` to redeem.",
                    inline=False)

                # Pause to let players see the 'typing' indicator
                # and drop the module
                await asyncio.sleep(1)
                await drop_channel.send(file=file, embed=embed)
                print("modules: Dropped %s in %s" % (module_id, drop_channel))


def setup(bot):
    bot.add_cog(Modules(bot))