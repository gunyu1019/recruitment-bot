import discord
import os

from discord.ext import interaction
from config.config import get_config
from config.log_config import log


if __name__ == "__main__":
    directory = os.path.dirname(os.path.abspath(__file__))
    parser = get_config("config")
    log.info("구인구직 봇을 불러오는 중입니다.")

    intent = discord.Intents().all()
    client = interaction.Client(
        intents=intent,
        global_sync_command=True,
        enable_debug_events=True
    )
    client.load_extensions("cogs", directory=directory)
    client.run(parser.get("Default", "token"))
