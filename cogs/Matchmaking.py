import random
import string
import os.path
import json
import datetime

from discord import TextChannel
from discord.ext import commands
from discord.ext.tasks import loop
from discord_components import Button, ButtonStyle
from discord import Embed as discord_embed
from discord.utils import get

from config import settings
from util.Match import Match


"""
Example of the structure of the json file for storing matches

self.match_data = {
    match_1_id: {
        player_1_id: {
            "damage": 750,
            "stuns": 4,
            "goons": 5,
            "points": 800,
            "elo": -19
        },
        player_2_id: {
            "damage": 750,
            "stuns": 7,
            "goons": 5,
            "points": 830,
            "elo": 19
        }
    }
}
"""

MATCHES_JSON_PATH = 'config/crane_matches_data.json'

class Matchmaking(commands.Cog):

    def __init__(self, bot):
    
        # init the bot instance
        self.bot = bot
        
        # init other cog instances
        self.competitive_cog = self.bot.get_cog('Competitive')
        
        # init all relevant channels
        self.match_create_channel: TextChannel = None
        self.ongoing_matches_channel: TextChannel = None
        self.match_results_channel: TextChannel = None
        
        # init all relevant messages
        self.match_create_message_id = None
        
        # init queues (TODO: split queues based on ranks)
        self.queue = []
        
        # init active matches dictionary
        self.active_matches = {}  # Match ID -> Match instance
        
        # includes all matches since the beginning of time
        # these matches are stored in a JSON file in config
        self.match_history = {}
        self.init_json_file()
        
    # TODO: idk, dev thing
    def check_json_file(self):
        need_save = False
        for mode in MODES:
            if mode not in self.rank_data:
                print(f"[Matchmaking.py] json missing mode: {mode}, initializing empty dict")
                self.rank_data[mode] = {}
                need_save = True

        if need_save:
            self.save_json_file()
        
    def init_json_file(self):

        if not os.path.exists(MATCHES_JSON_PATH):
            with open(MATCHES_JSON_PATH, 'w') as f:
                json.dump({}, f)

        with open(MATCHES_JSON_PATH) as f:
            self.match_history = json.load(f)
            print(f"[Matchmaking.py] Succecssfully loaded ranked data from {MATCHES_JSON_PATH}") 

        #self.check_json_file()

    def save_json_file(self):
        with open(MATCHES_JSON_PATH, 'w') as f:
            json.dump(self.match_history, f, indent=4)
            
    # updates the match history and saves it in the relevant JSON file
    def update_match_history(self, match):
    
        match_id = match.id
        
        player_dict = {}
        
        for player in match.competitors:
            player_dict[player] = match.competitors_info[player]
        
        if match_id not in self.match_history:
            self.match_history[match_id] = player_dict
        
        print(self.match_history)
        
        self.save_json_file()
                     
    @commands.Cog.listener()
    async def on_ready(self):
    
        # set all relevant channels upon startup
        self.match_create_channel = self.bot.get_channel(settings.MATCH_CREATE_CHANNEL)
        self.ongoing_matches_channel = self.bot.get_channel(settings.ONGOING_MATCHES_CHANNEL)
        self.match_results_channel = self.bot.get_channel(settings.MATCH_RESULTS_CHANNEL)

        # clear the match create channel
        await self.match_create_channel.purge()

        # create the queue embed and message
        button = [Button(style=ButtonStyle.green, label='Enter Queue', emoji='✅', custom_id=settings.MATCHMAKING_JOIN_QUEUE_CUSTOM_ID)]
        
        embed_title = "Entering the Queue"
        embed_desc = "**Enter Queue** using the button below!\n You will be matched with another player soon."
        
        embed = discord_embed(title=embed_title, description=embed_desc, color=0x4000ff)
        self.match_create_message_id = await self.match_create_channel.send("", embed=embed, components=button)

        # start the attempt create match loop
        self.attempt_create_match.start()


    # This loop is designed to run forever and attempts to create a match 
    # every T seconds, where T = settings.MATCHMAKING_CREATE_MATCH_FREQUENCY.
    # Perhaps later one we can randomize the time based on a certain range
    # to make it less predictable to match-make with someone directly
    @loop(seconds=settings.MATCHMAKING_CREATE_MATCH_FREQUENCY)
    async def attempt_create_match(self):

        print(f"[Matchmaking] attempting to create a match with {len(self.queue)} members")

        # TODO: rewrite this to accomodate for rank/elo-separated queues
        # Check if the queue(s) has enough players for matchmaking.
        if len(self.queue) <= 1:
            print("tried creating match with less than 2 members")
            return
            
        # Pick two random players from queue(s) and match them
        matched_players = random.sample(self.queue, 2)
        u1 = matched_players[0]
        u2 = matched_players[1]
        
        # Create the match(es)
        await self.create_match(u1, u2, 'craneduels')

    # This function generates a 6-character ID to represent a match
    def generate_match_id(self):
    
        # obtain list of characters (A-Z, 0-9)
        avail_chars = string.ascii_uppercase + string.digits
        
        # generate the unique ID for the match
        char_list = [] # list of characters to store in
        for _ in range(6): # loop to generate 6 random characters
            char_list.append(random.choice(avail_chars)) 
        generated_id = ''.join(char_list) # join all characters into a string

        # if the generated id is already in match history, generate again
        if generated_id not in self.match_history:
            return generated_id

        return self.generate_match_id()

    # function to handle entering the matchmaking queue
    def handle_enter_queue(self, player, mode_id):
    
        # TODO: add player to rank JSON if not already in
        if str(player.id) not in self.competitive_cog.rank_data[mode_id].keys():
            self.competitive_cog.add_player_to_data(mode_id, player.id)

        # TODO: find out which queue(s) this player fits in based on ELO
        
        # Check if player is in queues
        if player.id in self.queue:
            print(f"{player.display_name} tried joining the queue, but they are already in it!")
            return

        # Add player in all relevant queues
        self.queue.append(player.id)
        print(f"{player.display_name} with ID={player.id} has joined the queue")
        
    # function to obtain an active match's instance using the message ID
    def get_match(self, msg_id):
        for match in self.active_matches.values():
            if msg_id == match.message_id:
                return match
        return None

    # function to create a match with 2 randomly selected players
    async def create_match(self, u1, u2, mode_id):

        # generate random ID for match
        match_id = self.generate_match_id()
        
        # fetch player instances
        player_1 = await self.bot.fetch_user(u1)
        player_2 = await self.bot.fetch_user(u2)
        
        # fetch member instances and notify them that they've been matched
        guild = self.bot.get_guild(900290049147547689)
        member_1 = guild.get_member(u1)
        member_2 = guild.get_member(u2)
        score_report = f"Please contact them and conduct your match in-game. Once done, use your button in the #ongoing-matches channel to report your scores."
        await member_1.send(f"You've been matched with **{player_2.display_name}#{player_2.discriminator}**! {score_report}")
        await member_2.send(f"You've been matched with **{player_1.display_name}#{player_1.discriminator}**! {score_report}")

        # construct message buttons
        buttons = [
            Button(style=ButtonStyle.grey, label=f"{player_1.display_name} Submission", emoji='✅', custom_id=f"{settings.MATCHMAKING_ONGOING_CUSTOM_ID}{u1}"),
            Button(style=ButtonStyle.grey, label=f"{player_2.display_name} Submission", emoji='✅', custom_id=f"{settings.MATCHMAKING_ONGOING_CUSTOM_ID}{u2}")
        ]
        
        # construct message embed
        emoji = get(guild.emojis, name="vscl")
        embed_title = f"Match #{match_id}"
        embed_desc = f"**{player_1.display_name}** {emoji} **{player_2.display_name}**"
        
        embed = discord_embed(title=embed_title, description=embed_desc, color=0x4000ff)

        # construct and send ongoing match's message 
        msg = await self.ongoing_matches_channel.send(content="", embed=embed, components=buttons)

        # add match to dictionary of active matches
        self.active_matches[match_id] = Match(match_id, mode_id, msg.id, [u1, u2])

        # remove the players from the queue
        self.queue.remove(u1)
        self.queue.remove(u2)

    # function to determine winner and post/log match results
    async def handle_match_win(self, match):

        # obtain list of points, players, and mode ID
        points = match.competitors_points
        players = match.competitors
        mode_id = match.mode_id
        tie = False
        
        # if only one user has submitted the points, exit to wait for the next user
        if len(points.keys()) <= 1:
            print("Tried to determine winner with only 1 competitor's results")
            return

        # use this to convert users to members for message sending purposes 
        # member = guild.get_member(user_id) // member.send("msg")
        guild = self.bot.get_guild(900290049147547689)
 
        # invalid damage, notify users that the match will be cancelled
        if not match.is_total_damage_valid():
            for player in players:
                member = guild.get_member(player)
                await member.send("Something odd has been found with this match!\nThe match will be cancelled.")
                match.assign_elo_gain(player, 0)
            
            await self.delete_match(match)
            return

        # check if there is a tie
        if (max(points, key=points.get) == min(points, key=points.get)):
            tie = True
        
        # construct embed title
        results = ""
        for player in players:
            results += str(points[player])
            results += " - "

        embed_title = f"Match #{match.id} Results: {results[:-3]}"
        embed = discord_embed(title=embed_title, color=0x4000ff)
        
        # if there is no tie, perform elo calculations and post winner
        if not tie:
            # get winner and loser IDs based on points
            winner_id = max(points, key=points.get)
            loser_id = min(points, key=points.get)
            
            # fetch player instances 
            player_1 = await self.bot.fetch_user(winner_id)
            player_2 = await self.bot.fetch_user(loser_id)
            
            # get player elos
            p1_elo = self.competitive_cog.rank_data[mode_id][str(winner_id)]
            p2_elo = self.competitive_cog.rank_data[mode_id][str(loser_id)]
            
            # update player elos
            deltas = self.competitive_cog.get_delta(p1_elo, p2_elo, 30, 1)
            match.assign_elo_gain(winner_id, deltas[0])
            match.assign_elo_gain(loser_id, deltas[1])
            self.competitive_cog.update_elo(winner_id, mode_id, deltas[0])
            self.competitive_cog.update_elo(loser_id, mode_id, deltas[1])

            # Construct Match Result Embed
            embed.description = f"**{player_1.display_name}** won against **{player_2.display_name}**!"
        # if there is a tie
        else:
            # fetch player instances           
            player_1 = await self.bot.fetch_user(players[0])
            player_2 = await self.bot.fetch_user(players[1])
            
            match.assign_elo_gain(player_1.id, 0)
            match.assign_elo_gain(player_2.id, 0)
            
            # Construct Match Result Embed
            embed.description = f"**{player_1.display_name}** and **{player_2.display_name}** TIED!"

        # set embed time and send results in match results channel
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='\u200b')        
        msg = await self.match_results_channel.send(embed=embed)
        
        
        for player in players:
            member = guild.get_member(player)
            await member.send("The results have been posted in the #match-results channel!\n\nOptionally, please attach an in-game screenshot of your score numbers or video footage of the match, along with the match ID, in the #evidence-footage channel. Matches are subject to review and it is the responsibility of all competitors to provide insurance/confirmation of their matches in order to avoid their matches from being reverted if found guilty.")
        
        # delete Ongoing Match Msg from the Ongoing Matches Channel
        await self.delete_match(match)
        
    async def delete_match(self, match):
        
        # update Match History
        self.update_match_history(match)
        
        # remove match from active matches
        del self.active_matches[match.id]
        
        # delete match message from ongoing matches channel
        match_msg = await self.ongoing_matches_channel.fetch_message(match.message_id)
        await match_msg.delete()
        


def setup(bot):
    bot.add_cog(Matchmaking(bot))

