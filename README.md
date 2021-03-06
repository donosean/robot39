# robot39
Discord bot for the Channel 39 server dedicated to the Project Diva series, written using discord.py.
The bot is fairly server-specific and a lot of functions rely heavily on a postgreSQL database, the structure of which I haven't documented here, although a lot of the code could be repurposed for use in other Discord bots.

## Libraries Used
* [discord.py](https://github.com/Rapptz/discord.py)
* [psycopg2](https://github.com/psycopg/psycopg2)
* [natsort](https://github.com/SethMMorton/natsort)
* [iteration_utilities](https://github.com/MSeifert04/iteration_utilities)
* [Pillow](https://github.com/python-pillow/Pillow)

## Cogs
Each cog of the bot operates independantly and serves a different function. They are as follows:
* **autorole:** Allows for a specific role to be granted to new members automatically upon joining the server. This role can be customised on a per-server basis.
* **catwalk:** Sends reminder messages and role pings for an event that takes place in the server. Most likely too specific to be of use elsewhere.
* **duel:** Members of the server can 'duel' each other playing the Future Tone / Mega Mix rhythm games, being guided through these duels by the bot. Complete with a weighted ranking system based on the ELO formula used in chess and other competitive games. Probably the oldest/messiest code here.
* **database:** Contains the code used to connect to the postgreSQL database. The connection to this database is then accessible through a property of the Robot39 class.
* **events:** Writes to the terminal when basic events occur, such as a command being used or a new member joining a server the bot belongs to. Also responsible for setting the bot's custom status after logging in.
* **logging:** Sends messages to a (usually hidden) logging channel in the server to serve as an audit log. These messages are triggered by events such as messages being deleted or edited, members joining the server, new invites being created etc.
* **modules:** Collectible card game using the various modules/outfits from Future Tone / Mega Mix. "Cards" are pseudo-randomly dropped in a specific channel based on server message activity to be redeemed by server members, and can then be traded between members to complete sets.
* **nomimic:** Checks for changes in member nicknames to avoid members impersonating the bot.
* **owner:** Various functions designed only to be used by the 'owner' of the bot, such as loading/unloading cogs and sending messages through the bot's user.
* **quotes:** Server admins can have messages from server members sent as embeds to a specific channel in a 'quote' format. Mainly a server-specific novelty.
* **streaming:** Listens for a change in any server member's streaming activity on Discord, granting/removing a specific role based on whether they are live-streaming or not. This allows any members that are currently streaming to be 'hoisted' to the top of the server's online member list to provide their stream with more visibililty.
