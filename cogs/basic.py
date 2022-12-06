import logging
import discord
from discord.ext import interaction
from config.config import get_config

logger = logging.getLogger(__name__)
logger_command = logging.getLogger(__name__ + ".command")
parser = get_config("config")


class Basic:
    def __init__(self, client):
        self.client = client
        self.color = int(parser.get("Default", "color"), 16)

    @interaction.listener()
    async def on_ready(self):
        logger.info(f"디스코드 봇 로그인이 완료되었습니다.")
        logger.info(f"디스코드봇 이름: {self.client.user.name}")
        logger.info(f"디스코드봇 ID: {str(self.client.user.id)}")
        logger.info(f"디스코드봇 버전: {discord.__version__}")

    @interaction.listener()
    async def on_interaction_command(self, ctx: interaction.ApplicationContext):
        if ctx.guild is not None:
            logger_command.info(f"({ctx.guild} | {ctx.channel} | {ctx.author}) {ctx.content}")
        else:
            logger_command.info(f"(DM채널 | {ctx.author}) {ctx.content}")

    @interaction.command(name="초대링크")
    async def invite(self, ctx: interaction.ApplicationContext):
        embed = discord.Embed(
            title='구인구직봇 초대링크',
            description='https://c11.kr/11j0i',
            colour=self.color
        )
        await ctx.send(embed=embed)

    @interaction.command(name="핑")
    async def ping(self, ctx: interaction.ApplicationContext):
        embed = discord.Embed(
            title=f'{round(self.client.latency * 1000)}ms',
            description='현재 핑입니다.',
            colour=self.color
        )
        await ctx.send(embed=embed)


def setup(client: interaction.Client):
    client.add_interaction_cog(Basic(client))
