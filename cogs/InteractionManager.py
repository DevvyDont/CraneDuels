from discord.ext import commands
from discord_components import Interaction

from config import settings


class InteractionManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):

        matchmaking_cog = self.bot.get_cog('Matchmaking')
        competitive_cog = self.bot.get_cog('Competitive')
        player = await self.bot.fetch_user(interaction.user.id)
        guild = self.bot.get_guild(900290049147547689)
        member = guild.get_member(interaction.user.id)
        mode_id = None
        
        for mode in competitive_cog.rank_data.keys():
            if mode in settings.MATCHMAKING_JOIN_QUEUE_CUSTOM_ID:
                mode_id = mode

        if interaction.custom_id == settings.MATCHMAKING_JOIN_QUEUE_CUSTOM_ID:
            matchmaking_cog.handle_enter_queue(player, mode_id)

        if settings.MATCHMAKING_ONGOING_CUSTOM_ID in interaction.custom_id:


            match = matchmaking_cog.get_match(interaction.message.id)
            if str(interaction.user.id) not in interaction.custom_id:
                print(f"User {interaction.user.id} tried to dictate result of a match they're not part of")
                return
                        
            def check(msg):
                return msg.author == player

            msg = f"```Match #{match.id} Results\n\nfor player: {player.display_name} with ID={player.id}```\n**Please enter your damage: **"
            await member.send(msg)
            dmg_msg = await self.bot.wait_for('message', check=check)
            damage = int(str(dmg_msg.content))

            msg = f"**Please enter your number of stuns: **"
            await member.send(msg)
            stuns_msg = await self.bot.wait_for('message', check=check)
            stuns = int(str(stuns_msg.content))

            msg = f"**Please enter your number of goons stomped: **"
            await member.send(msg)
            goons_msg = await self.bot.wait_for('message', check=check)
            goons = int(str(goons_msg.content))
            
            points = match.calculate_total_points(damage, stuns, goons)
            match.assign_player_points(player.id, damage, stuns, goons)
            
            await matchmaking_cog.handle_match_win(match)

def setup(bot):
    bot.add_cog(InteractionManager(bot))

