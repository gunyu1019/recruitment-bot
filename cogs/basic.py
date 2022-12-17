import asyncio
import logging
import datetime
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

    @interaction.command(name="초대링크", description="초대링크를 불러옵니다.")
    async def invite(self, ctx: interaction.ApplicationContext):
        embed = discord.Embed(
            title='구인구직봇 초대링크',
            description='https://c11.kr/11j0i',
            colour=self.color
        )
        message = await ctx.send(embed=embed)
        await asyncio.sleep(
            parser.getint("DelayDelete", "invite")
        )
        await message.delete()

    @interaction.command(name="핑", description="봇의 응답 속도를 불러옵니다.")
    async def ping(self, ctx: interaction.ApplicationContext):
        datetime_now_for_read = datetime.datetime.now(tz=datetime.timezone.utc)
        embed = discord.Embed(
            title='현재 핑 입니다.',
            colour=self.color
        )
        embed.add_field(name="지연 속도", value=f'{round(self.client.latency * 1000)}ms', inline=True)
        embed.add_field(
            name="응답 속도",
            value=f'읽기 속도: {abs(round((ctx.created_at - datetime_now_for_read).total_seconds() * 1000))}ms',
            inline=True
        )
        message = await ctx.send(embed=embed)
        datetime_now_for_write = datetime.datetime.now(tz=datetime.timezone.utc)

        embed.set_field_at(
            index=1,
            name=embed.fields[1].name,
            value=f'{embed.fields[1].value}\n'
                  f'쓰기 속도: : {abs(round((datetime_now_for_write - message.created_at).total_seconds() * 1000))}ms',
            inline=embed.fields[1].inline
        )
        await message.edit(embed=embed)
        await asyncio.sleep(
            parser.getint("DelayDelete", "ping")
        )
        await message.delete()


def setup(client: interaction.Client):
    client.add_interaction_cog(Basic(client))
