from discord import Embed
from discord.ext import commands
from datetime import datetime
from config import settings

TOP_N = 5  # How many users to display on the leaderboards

MODE_CRANE = 'craneduels'
MODE_UNO = 'uno'

MODES = {
    # MODE_UNO: "Toono",
    MODE_CRANE: "Crane Duels"
}

class LeaderboardManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.placements = {}

    @commands.Cog.listener()
    async def on_ready(self):
    
        self.competitive = self.bot.get_cog('Competitive')
        self.leaderboards_channel = self.bot.get_channel(settings.LEADERBOARDS_CHANNEL)
        
        for mode_id in MODES:
            await self.update_leaderboard(mode_id)
        
    # Updates the leaderboard of the given mode
    async def update_leaderboard(self, mode_id):
        await self.leaderboards_channel.purge()
        thumbnail = settings.THUMBNAILS[mode_id]
        color = settings.COLORS[mode_id]
        embed = Embed(title="Crane Duels Leaderboard", color=color)
        embed.set_thumbnail(url=thumbnail)
        leaderboard_text = ""
        
        player_data = self.competitive.rank_data[mode_id]
        print(player_data)
        
        if not player_data:
            leaderboard_text += "Nobody is ranked yet :(\n"
        else:
            player_data = self.competitive.rank_data[mode_id]
            
            ordered = dict(sorted(player_data.items(), key=lambda pelo:pelo[1], reverse=True))
            place = 1
            for id, elo in ordered.items():
                member = await self.bot.fetch_user(int(id))
                name = str(member) if member else f"Unknown ({id})"
                rank, div = self.competitive.get_rank_from_elo(elo)
                leaderboard_text += f"{place}: {name} - {rank} {div}\n"
                place += 1
                if place >= TOP_N:
                    break
        embed.description = leaderboard_text
        await self.leaderboards_channel.send("", embed=embed)

def setup(bot):
    bot.add_cog(LeaderboardManager(bot))
