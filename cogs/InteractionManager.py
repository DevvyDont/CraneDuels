from discord.ext import commands
from discord_components import Interaction

from config import settings


class InteractionManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, interaction: Interaction):

        matchmaking_cog = self.bot.get_cog('Matchmaking')

        if interaction.custom_id == settings.MATCHMAKING_JOIN_QUEUE_CUSTOM_ID:
            matchmaking_cog.handle_enter_queue(interaction.user.id)


def setup(bot):
    bot.add_cog(InteractionManager(bot))

