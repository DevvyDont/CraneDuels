import random
import string

from discord import TextChannel
from discord.ext import commands
from discord.ext.tasks import loop
from discord_components import Button, ButtonStyle
from discord import Embed as discord_embed

from config import settings
from util.Match import Match


class Matchmaking(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.match_create_channel: TextChannel = None
        self.ongoing_matches_channel: TextChannel = None
        self.match_results_channel: TextChannel = None
        self.match_create_message_id = None

        self.queue = []

        self.active_matches = {}  # Match ID -> Match instance

    @commands.Cog.listener()
    async def on_ready(self):
        self.match_create_channel = self.bot.get_channel(settings.MATCH_CREATE_CHANNEL)
        self.ongoing_matches_channel = self.bot.get_channel(settings.ONGOING_MATCHES_CHANNEL)
        self.match_results_channel = self.bot.get_channel(settings.MATCH_RESULTS_CHANNEL)

        # Clear the match create channel
        await self.match_create_channel.purge()

        button = [Button(style=ButtonStyle.green, label='Enter Queue', emoji='✅', custom_id=settings.MATCHMAKING_JOIN_QUEUE_CUSTOM_ID)]

        # create the queue message
        
        embed_title = "Entering the Queue"
        embed_desc = "Please press the **Enter Queue** button below to enter the queue! You will be matched with another player within the queue soon."
        
        embed = discord_embed(title=embed_title, description=embed_desc, color=0x4000ff)
        self.match_create_message_id = await self.match_create_channel.send("", embed=embed, components=button)

        # Start the attempt create match loop
        self.attempt_create_match.start()

    def handle_enter_queue(self, user_id):

        if user_id in self.queue:
            print(f"tried adding {user_id} to queue but they are already in it")
            return

        self.queue.append(user_id)
        print(f"{user_id} has joined the queue")

    async def handle_match_win(self, match, custom_id):

        winner_id = None
        loser_id = None
        
        if custom_id:
            winner_id = custom_id.replace(settings.MATCHMAKING_ONGOING_CUSTOM_ID, '')
            for id in match.competitors:
                if id != winner_id:
                    loser_id = id

        embed_title = f"Match #{match.id} Results"
        embed_desc = f"User {winner_id} won against {loser_id}!"
        
        embed = discord_embed(title=embed_title, description=embed_desc, color=0x4000ff)
        
        if winner_id:
            msg = await self.match_results_channel.send(embed=embed)

        del self.active_matches[match.id]
        
        match_msg = await self.ongoing_matches_channel.fetch_message(match.message_id)
        await match_msg.delete()

    @loop(seconds=settings.MATCHMAKING_CREATE_MATCH_FREQUENCY)
    async def attempt_create_match(self):

        print(f"[Matchmaking] attempting to create a match with {len(self.queue)} members")

        if len(self.queue) <= 1:
            print("tried creating match with less than 2 members")
            return
            
        #split queues later on based on rank/elo
        matched_players = random.sample(self.queue, 2)
        u1 = matched_players[0]
        u2 = matched_players[1]
        await self.create_match(u1, u2)

    def generate_match_id(self):
        avail_chars = string.ascii_uppercase + string.digits
        id_list = []
        for _ in range(6):
            id_list.append(random.choice(avail_chars))
        generated_id = ''.join(id_list)

        if generated_id not in self.active_matches:
            return generated_id

        return self.generate_match_id()
        
    def get_match(self, msg_id):
        for match in self.active_matches.values():
            if msg_id == match.message_id:
                return match
        return None

    async def create_match(self, u1, u2):

        match_id = self.generate_match_id()

        buttons = [
            Button(style=ButtonStyle.grey, label=f"{u1} won", emoji='✅', custom_id=f"{settings.MATCHMAKING_ONGOING_CUSTOM_ID}{u1}"),
            Button(style=ButtonStyle.grey, label=f"{u2} won", emoji='✅', custom_id=f"{settings.MATCHMAKING_ONGOING_CUSTOM_ID}{u2}")
        ]
        
        embed_title = f"Match #{match_id}"
        embed_desc = f"{u1} VS {u2}"
        
        embed = discord_embed(title=embed_title, description=embed_desc, color=0x4000ff)

        msg = await self.ongoing_matches_channel.send(content="", embed=embed, components=buttons)

        self.active_matches[match_id] = Match(match_id, msg.id, [u1, u2])

        # remove them from the queue
        self.queue.remove(u1)
        self.queue.remove(u2)


def setup(bot):
    bot.add_cog(Matchmaking(bot))

