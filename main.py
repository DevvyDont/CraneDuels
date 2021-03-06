import traceback

import discord

from config import settings
from discord.ext import commands

from discord_components import ComponentsBot



def main():

    intents = discord.Intents.default()
    intents.members = True

    bot = ComponentsBot(command_prefix='!', intents=intents)
    # bot.remove_command('help')  --We will make our own help command later


    @bot.event
    async def on_ready():
        print(f"Successfully logged in as {bot.user}")

    for ext in settings.EXTENSIONS:
        try:
            bot.load_extension(f"cogs.{ext}")
            print(f"Successfully loaded the '{ext}' extension!")
        except Exception as e:
            traceback.print_exc()
            print(f"Failed to load the '{ext}' extension!\n{e}")

    # Make sure that you have a file in your 'config' folder named 'token.txt' with your bot's token inside
    try:
        with open('config/token.txt', 'r') as f:
            bot.run(f.read())
    except FileNotFoundError:
        input('[FATAL]: "token.txt" does not exist! Make sure you make a txt file in the "config" folder containing your bots token!')


if __name__ == '__main__':
    main()


