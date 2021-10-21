from discord import Embed
from discord.errors import InvalidArgument
from discord.ext import commands
import json

import os.path

from discord.ext.commands.core import command

DEBUG = True


"""
Example of the structure of the json file for storing elos
If we ever want to add a new mode we can just add a new enum to use

self.rank_data = {
    MODE_UNO: {
        123456789: 420,
        987654321: 690
    },

    MODE_CRANE: {
        123456789: 888,
        019293848: 1000
    }
}
"""

MODE_CRANE = 'craneduels'
MODE_UNO = 'uno'

MODES = {
    # MODE_UNO: "Toono",
    MODE_CRANE: "Crane Duels"
}

ELO_JSON_PATH = 'config/competitive_rank_data.json'

DEFAULT_ELO = 650
MINIMUM_ELO = 300
SOFT_CAP_ELO = 2000
MAX_ELO = 100000  # Need this just for sanity purposes

RANK_RANGES = (
    ("Silver",      MINIMUM_ELO,    600         ),
    ("Gold",        601,            950         ),
    ("Platinum",    951,            1400        ),
    ("Diamond",     1401,           SOFT_CAP_ELO),
    ("Grandmaster", SOFT_CAP_ELO+1, MAX_ELO     )
)

def getRankFromElo(elo: int):
    elo = min(elo, MAX_ELO)
    elo = max(elo, MINIMUM_ELO)

    for rank_tuple in RANK_RANGES:
        name, low, high = rank_tuple
        if low <= elo <= high:
            percent_through_rank = (elo-low)/(high-low) 
            div = 1
            if percent_through_rank > .33:
                div += 1
            if percent_through_rank > .66:
                div += 1
            return name, div if elo <= SOFT_CAP_ELO else ""
    
    raise InvalidArgument(f"Received elo out of bounds: {elo}")

class Competitive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rank_data = {}  # Stores a dict that maps game/mode enum -> another dict thats ID -> elo, example of structure is above class decl
        self.init_json_file()


    # Checks the json file to make sure all games exist, fixes it if we're missing something
    def check_json_file(self):
        need_save = False
        for mode in MODES:
            if mode not in self.rank_data:
                print(f"[Competitive.py] json missing mode: {mode}, initializing empty dict")
                self.rank_data[mode] = {}
                need_save = True

        if need_save:
            self.save_json_file()
        

    def init_json_file(self):

        if not os.path.exists(ELO_JSON_PATH):
            with open(ELO_JSON_PATH, 'w') as f:
                json.dump({}, f)

        with open(ELO_JSON_PATH) as f:
            self.rank_data = json.load(f)
            print(f"[Competitive.py] Succecssfully loaded ranked data from {ELO_JSON_PATH}") 

        self.check_json_file()

           

    def save_json_file(self):
        with open(ELO_JSON_PATH, 'w') as f:
            json.dump(self.rank_data, f, indent=4)

    # Used to retrive the ELO of a user, take in discord id and the enum for what mode/game
    def get_elo(self, user_id, mode_id):
        mode_dict: dict = self.rank_data.get(mode_id)
        # If the user isn't in there, they are default elo
        return mode_dict.get(str(user_id), DEFAULT_ELO)

    # Used to retrieve all ELOs of a user, returns a dict that maps mode id -> elo
    def get_all_elos(self, user_id):
        ret = {}

        for mode, mode_data in self.rank_data.items():
            ret[mode] = mode_data.get(str(user_id), DEFAULT_ELO)

        return ret

    # Updates a users elo in a given mode and changes it by delta, e.g. to increase someones elo by 5 make delta=5
    def update_elo(self, user_id, mode_id, delta):
        old = self.get_elo(user_id, mode_id)  # Get elo
        elo = old
        elo += delta  # Update elo
        if elo <= MINIMUM_ELO:  # Don't let them go below the cap
            elo = MINIMUM_ELO

        self.rank_data[mode_id][str(user_id)] = elo  # Update 
        self.save_json_file()  # Save the json file with our changes
        return elo

    @commands.command(name='leaderboard')
    async def _command_leaderboard(self, ctx):

        msg = "```"

        for mode, player_data in self.rank_data.items():

            msg += f"{MODES[mode]}\n----------------------\n"
            if not player_data:
                msg += "Nobody is ranked yet :(\n"

            ordered = dict(sorted(player_data.items(), key=lambda pelo: pelo[1], reverse=True))
            place = 1
            for id, elo in ordered.items():
                member = await self.bot.fetch_user(int(id))
                name = str(member) if member else f"Unknown ({id})"
                rank, div = getRankFromElo(elo)
                msg += f"{place}: {name} - {rank} {div} ({elo})\n"
                place += 1
            msg += "----------------------\n\n"

        msg += "```"
        await ctx.send(msg)


    @commands.command(name='rank')
    async def _command_rank(self, ctx):
        elos = self.get_all_elos(ctx.author.id)
        msg = ""
        for game, elo in elos.items():
            rank, div = getRankFromElo(elo)
            msg += f"**{MODES[game]}**: `{rank} {div}` ({elo})\n"

        await ctx.send(f"{ctx.author.mention}\n{msg}")

    if DEBUG:
        @commands.command(name='elochange')
        async def _command_elochange(self, ctx, mode=None, delta: int=None):

            if not mode or not delta:
                await ctx.send(f"Command usage: `!elochange [{' | '.join([m for m in MODES.keys()])}] <amount to change by>`")
                return

            if mode not in MODES:
                await ctx.send("Invalid mode: `" + mode + "`")
                return

            new_elo = self.update_elo(ctx.author.id, mode, delta)
            rank, div = getRankFromElo(new_elo)
            await ctx.send(f"New elo for `{MODES[mode]}` is `{new_elo} ({rank} {div})`")


def setup(bot):
    bot.add_cog(Competitive(bot))

