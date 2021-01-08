import asyncio
import secrets

async def can_duel(self, ctx, player1, player2):
    #check if new duels are enabled
    if not self.duels_enabled:
        await ctx.send("New duels are temporarily disabled, most likely due to testing new features. Please go bother Seán if this lasts more than a few minutes.")
        print("duel: Duels are disabled.")
        return False

    #only begin duel in allowed channels
    if ctx.channel.id not in self.duel_channels:
        await ctx.send("Please only use the 39!challenge command in a duel channel, %s." % player1.mention)
        print("duel: challenge command used outside of valid channel.")
        return False
    
    #one duel per channel
    if ctx.channel.id in self.duels_in_progress:
        await ctx.send("There is already a duel in progress or pending challenge here, %s." % player1.mention)
        print("duel: Duel already in progress in channel %s" % ctx.channel)
        return False

    #various checks to make sure both players are registered and not bots
    if player1 == player2:
        await ctx.send("You can't challenge yourself, %s!" % player1.mention)
        print("duel: Player %s attempted to challenge themself." % player1)
        return False

    if player2 == self.bot.user:
        joke_emoji = self.bot.get_emoji(self.joke_emoji)
        await ctx.send("Oh? You're approaching me? %s" % str(joke_emoji))
        print("duel: %s???" % player1)
        #no return statement here so next check can run

    if player2.bot:
        await ctx.send("You can't challenge a bot, %s!" % player1.mention)
        print("duel: Player %s challenged a bot." % player1)
        return False
    
    if not await self.is_registered(player1):
        await ctx.send("You must be registered to challenge someone, %s! Please use command 39!register." % player1.mention)
        print("duel: Player %s is not registered." % player1)
        return False
    
    if not await self.is_registered(player2):
        await ctx.send("%s is not registered, %s! Please ask them to use command 39!register before challenging them." % (str(player2), player1.mention))
        print("duel: Player %s challenged %s who is not registered." % (player1, player2))
        return False
    
    else:
        return True

async def get_shared_songs(self, player1, player2):
    async def get_player_songs(player_dlc):
        songs = []

        if not player_dlc:
            return songs

        for song in self.songs:
            for dlc in player_dlc:
                if song[dlc] == '✓':
                    songs.append("%s \ %s" % (song['Eng Title'], song['JP Title']))
        
        return songs
    
    p1_info = await self.fetch_players(player1.id)
    p2_info = await self.fetch_players(player2.id)

    p1_songs = await get_player_songs(p1_info[6])
    p2_songs = await get_player_songs(p2_info[6])

    shared_set = set(p1_songs).intersection(p2_songs)
    shared_songs = list(shared_set)

    print("duel: Generated list of %s shared song(s) between %s and %s." % (len(shared_songs), player1, player2))
    return shared_songs

async def get_max_points(self, ctx, duel_type):
    duel_type = duel_type.lower()
    return\
        2 if duel_type == "bo3" else\
        3 if duel_type == "bo5" else\
        5 if duel_type == "bo9" else False

async def issue_challenge(self, ctx, player1, player2, duel_type):
    #emoji for reacts
    yes = self.bot.get_emoji(self.yes_emoji)
    no = self.bot.get_emoji(self.no_emoji)

    #issue challenge message to player
    challenge_message = await ctx.send("%s! You've been challenged to a best of %s by %s! React below with %s to accept or %s to decline.\n"\
        % (player2.mention, duel_type[2:], player1.mention, str(yes), str(no))\
        + "*This challenge will expire in one minute.*")

    #add reactions for accept/decline
    await challenge_message.add_reaction(yes)
    await challenge_message.add_reaction(no)

    #return message id to be used in checks
    return challenge_message.id

async def confirm_duel(self, ctx, player1, player2, challenge_id):
    #emoji for reacts
    yes = self.bot.get_emoji(self.yes_emoji)
    no = self.bot.get_emoji(self.no_emoji)

    #checks for the following:
    # -- reaction must be by player2
    # -- reaction must be yes or no
    # -- reaction must be on the message issued by the bot
    def check(reaction, user):
        return user == player2\
            and (str(reaction.emoji) == str(yes) or (str(reaction.emoji) == str(no)))\
            and reaction.message.id == challenge_id

    #get message object so that it can be edited and have reacts removed
    challenge_message = await ctx.channel.fetch_message(challenge_id)

    #logic for awaiting/dealing with reactions
    try:
        reaction = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
    
    except asyncio.TimeoutError:
        await challenge_message.edit(content="%s! You've been challenged by %s!\n"\
            % (player2.mention, player1.mention)\
            + "*This challenge has now expired.*")
    
        #avoids the current duel channel being softlocked if the challenge expires
        if ctx.channel.id in self.duels_in_progress:
            self.duels_in_progress.remove(ctx.channel.id)

        #return false since duel was not accepted
        return False

    else :
        await challenge_message.edit(content="%s! You've been challenged by %s!\n*%s*"\
            % (player2.mention, player1.mention, "Challenge accepted!" if str(reaction[0]) == str(yes) else "Challenge declined."))

        if str(reaction[0]) == str(no)\
            and ctx.channel.id in self.duels_in_progress:
            self.duels_in_progress.remove(ctx.channel.id)

        #duel can continue if accepted, otherwise end it
        return True if str(reaction[0]) == str(yes) else False
    
    finally:
        #remove bot reactions
        await challenge_message.remove_reaction(yes, self.bot.user)
        await challenge_message.remove_reaction(no, self.bot.user)

async def begin_round(self, ctx, player1, player2, duel_round, shared_songs_list):
    #emoji for reacts
    yes = self.bot.get_emoji(self.yes_emoji)
    
    #roll a random song from the shared song list
    rolled_song = secrets.choice(shared_songs_list)

    #the player being challenged gets to roll on odd rounds
    duel_message = await ctx.send("**Round #%s**\n" % duel_round\
        +"Your song for this round is: **%s**!\nBoth players react with %s below when you're ready to play.\n"\
        % (rolled_song, str(yes))\
        + "Countdown will begin upon confirming.\n"\
        + "*You have three minutes to confirm.*")

    #reaction for players to ready up
    await duel_message.add_reaction(yes)

    #variables for check
    check_id = duel_message.id

    #checks for the following:
    # -- player1 or player 2 reacts
    # -- yes only
    def check_p1(reaction, user):
        return user == player1\
            and (str(reaction.emoji) == str(yes))\
            and reaction.message.id == check_id
    # -- same as above
    def check_p2(reaction, user):
            return user == player2\
                and (str(reaction.emoji) == str(yes))\
                and reaction.message.id == check_id

    #allows bot to send message after each ready up react
    async def player_confirm(player):
        await self.bot.wait_for('reaction_add', timeout=180.0,\
            check=check_p1 if player == player1 else check_p2)

        await ctx.send("%s is ready!" % player.mention)

    #logic for awaiting/dealing with reactions
    try:
        #wait for both players to react
        await asyncio.gather(
            player_confirm(player1),
            player_confirm(player2)
        )
        
    except asyncio.TimeoutError:
        #player(s) didn't react on time
        await duel_message.edit(content="*The round timed out.*")

        #ends duel
        return False

    else :
        #players confirmed as ready, duel continues
        return True
    
    finally:
        #remove bot reacts
        await duel_message.remove_reaction(yes, self.bot.user)

async def song_countdown(self, ctx):
    countdown = 5
    countdown_message = await ctx.send("Song confirmed, get ready to begin!\nStart in")

    while (countdown > 0):
        await countdown_message.edit(content=(countdown_message.content + " %s..." % countdown))
        countdown -= 1
        await asyncio.sleep(1)

    await countdown_message.edit(content=(countdown_message.content + " **Go!**"))

async def confirm_scores(self, ctx, player1, player2):
    #emoji for reacts
    yes = self.bot.get_emoji(self.yes_emoji)

    #post message prompting upload of score image from both players
    finished_message = await ctx.send("Please upload a screenshot or photo of your results screen.\n"\
    + "React below with %s to confirm posting your score.\n" % str(yes)\
    + "*You have five minutes to upload from the time this message appears.*")

    #reaction for players to confimr
    await finished_message.add_reaction(yes)

    #variables for check
    check_id = finished_message.id

    #checks for the following:
    # -- player1 or player 2 reacts
    # -- yes only
    def check_p1(reaction, user):
        return user == player1\
            and (str(reaction.emoji) == str(yes))\
            and reaction.message.id == check_id
    # -- same as above
    def check_p2(reaction, user):
            return user == player2\
                and (str(reaction.emoji) == str(yes))\
                and reaction.message.id == check_id

    #allows bot to send message after each ready up react
    async def player_confirm(player):
        await self.bot.wait_for('reaction_add', timeout=300.0,\
            check=check_p1 if player == player1 else check_p2)

        await ctx.send("%s has confirmed posting their score!" % player.mention)

    #logic for awaiting/dealing with reactions
    try:
        #wait for both players to react
        await asyncio.gather(
            player_confirm(player1),
            player_confirm(player2)
        )

    except asyncio.TimeoutError:
        await finished_message.edit(content="*The round timed out.*")
        return False

    else :
        #both players have confirmed posting scores, continue round
        return True
    
    finally:
        #remove bot reactions
        await finished_message.remove_reaction(yes, self.bot.user)

async def get_winner(self, ctx, player1, player2):
    #emoji for reacts
    yes = self.bot.get_emoji(self.yes_emoji)   
    
    win_message = await ctx.send("Please react below with %s if you are the **winner** of this round.\n"\
        % str(yes)\
        + "The other player **will** be asked to confirm this.\n"\
        + "*You have one minute to confirm.*")

    #reaction for players to confirm
    await win_message.add_reaction(yes)

    #checks for the following:
    # -- only player1 or player2
    # -- reaction must be yes
    # -- reaction must be on the message issued by the bot
    def check(reaction, user):
        return (user == player1 or user == player2)\
            and str(reaction.emoji) == str(yes)\
            and reaction.message.id == win_message.id 

    try:
        reaction = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        round_winner = reaction[1]
    
    except asyncio.TimeoutError:
        await win_message.edit(content="*The round timed out.*")
        return 0

    else:
        #return number of winning player (p1=1, p2=2)
        return 1 if round_winner == player1 else 2

    finally:
        #remove bot reactions
        await win_message.remove_reaction(yes, self.bot.user)

async def confirm_winner(self, ctx, winner, loser):
    #emoji for reacts
    yes = self.bot.get_emoji(self.yes_emoji)
    no = self.bot.get_emoji(self.no_emoji)

    #prompt other player to confirm the winner
    confirm_message = await ctx.send("%s, can you confirm that %s is the winner of this round?\n"\
        % (loser.mention, winner.mention)\
        + "React with %s for yes or %s for no.\n"\
        % (str(yes), str(no))\
        + "*You have one minute to confirm.*")

    #reactions for player response
    await confirm_message.add_reaction(no)
    await confirm_message.add_reaction(yes)
    
    #only listen for reacts from the confirming player
    def check(reaction, user):
        return user == loser\
            and (str(reaction) == str(yes) or str(reaction) == str(no))\
            and reaction.message.id == confirm_message.id

    try:
        reaction = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

    except asyncio.TimeoutError:
        #player didn't react on time
        return False

    else:
        #confirming player has reacted
        return True if str(reaction[0]) == str(yes) else False
    
    finally:
        #remove bot reactions
        await confirm_message.remove_reaction(no, self.bot.user)
        await confirm_message.remove_reaction(yes, self.bot.user)

async def process_duel_results(self, ctx, winner, loser, duel_max_points=2):
    #fetch player info
    player1 = await self.fetch_players(winner.id)
    player2 = await self.fetch_players(loser.id)

    #set weighting/multipler depending on duel length
    multiplier = \
        1 if duel_max_points == 2 else\
        1.5 if duel_max_points == 3 else\
        2.5 if duel_max_points == 5 else 1

    #calculate new elo
    p1_elo = player1[2]
    p2_elo = player2[2]
    win_points = await self.calculate_elo(p1_elo, p2_elo, multiplier)

    p1_new_elo = p1_elo + win_points
    p2_new_elo = p2_elo - win_points

    #commit new elo to db
    await self.update_points(winner.id, p1_new_elo, player_win = True)
    await self.update_points(loser.id, p2_new_elo, player_win = False)

    #announce new elo
    await ctx.send("**Rank change!**\n"\
        + "%s: %s -> %s\n" % (winner.mention, p1_elo, p1_new_elo)\
        + "%s: %s -> %s" % (loser.mention, p2_elo, p2_new_elo))

    #record duel details to db
    await self.record_duel(winner.id, p1_new_elo, loser.id, p2_new_elo, win_points)