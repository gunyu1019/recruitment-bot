import asyncio
import datetime
import json
import copy
import os

import discord
from discord.state import ConnectionState
from discord.ext import interaction
from typing import Union, List, Dict

from config.config import get_config
from utils.directory import directory

parser = get_config("config")
comment_parser = get_config("comment")
data_type = Union[str, discord.Guild, discord.Member, discord.TextChannel, discord.PartialMessage, datetime.datetime]


class Recruitment:
    def __init__(self, client: interaction.Client):
        self.client = client
        self.color = int(parser.get("Default", "color"), 16)

        if parser.has_option("Default", "channels"):
            self.has_recruitment_channel = True
            self.recruitment_channel = json.loads(parser.get("Default", "channels"))
        else:
            self.has_recruitment_channel = False
            self.recruitment_channel = []
        self.pending_recruitment = {}

        self.comment_unlimited = comment_parser.get("Recruitment", "unlimited")

    @interaction.listener()
    async def on_ready(self):
        pending_recruitment_from_data = self.load_pending_recruitment()
        await self.pending_recruitment_init(pending_recruitment_from_data)

    def voice_channel_formatter(self, regex: str, info: discord.VoiceChannel):
        return regex.format(
            channel_name=info.name,
            channel_id=info.id,
            channel_mention=info.mention,
            category_name=getattr(info.category, "name", "No Category"),
            category_id=getattr(info.category, "id", "No Category Id"),
            category_mention=getattr(info.category, "mention", "No Category"),
            current=f"{len(info.members)}명",
            limit=f"{info.user_limit}명" if info.user_limit > 0 else self.comment_unlimited
        )

    def voice_channel_member_count_formatter(self, regex: str, info: discord.VoiceChannel):
        return regex.format(
            current=f"{len(info.members)}명",
            limit=f"{info.user_limit}명" if info.user_limit > 0 else self.comment_unlimited
        )

    @staticmethod
    def author_formatter(regex: str, info: discord.Member):
        return regex.format(
            author_mention=info.mention,
            author_name=f"{info.name}#{info.discriminator}",
            author_id=info.id
        )

    def save_pending_recruitment(self):
        _pending_recruitment = {}
        for (key, value) in self.pending_recruitment.items():
            _pending_recruitment[key] = {
                "requester": value["requester"].id,
                "guild": value["guild"].id,
                "channel": value["channel"].id,
                "message": value["message"].id,
                "created_at": value["created_at"].timestamp()
            }
        with open(os.path.join(directory, "data", "pending_recruitment.json"), mode="w") as fp:
            fp.write(json.dumps(_pending_recruitment, indent=4))
        return

    def load_pending_recruitment(self) -> List[Dict[str, data_type]]:
        pending_recruitment_from_data = []
        with open(os.path.join(directory, "data", "pending_recruitment.json"), mode="r") as fp:
            _pending_recruitment = json.load(fp)
            for (key, value) in _pending_recruitment.items():
                guild: discord.Guild = self.client.get_guild(value["guild"])
                requester: discord.Member = guild.get_member(value["requester"])
                channel: discord.TextChannel = guild.get_channel(value["channel"])
                message = channel.get_partial_message(value["message"])
                _datetime = datetime.datetime.fromtimestamp(value["created_at"], tz=datetime.timezone.utc)
                data = {
                    "requester": requester,
                    "guild": guild,
                    "channel": channel,
                    "message": message,
                    "create_at": _datetime
                }
                self.pending_recruitment[key] = data
                pending_recruitment_from_dt = copy.copy(data)
                pending_recruitment_from_dt["voice_channel"] = key
                pending_recruitment_from_data.append(pending_recruitment_from_dt)
        return pending_recruitment_from_data

    async def pending_recruitment_init(self, pending_recruitment):
        pending_recruitment_from_data = copy.copy(pending_recruitment)
        if len(pending_recruitment_from_data) > 0:
            pending_recruitment_from_data = sorted(pending_recruitment_from_data, key=lambda it: it["create_at"].timestamp())
            pending_recruitment_from_data.reverse()

            item = pending_recruitment_from_data.pop()
            while True:
                datetime_now = datetime.datetime.now(tz=datetime.timezone.utc)
                if item["create_at"].timestamp() + 30 - datetime_now.timestamp() < 0:
                    try:
                        await item["message"].delete()
                        self.pending_recruitment.pop(item["voice_channel"])
                    except discord.NotFound:
                        pass

                    if len(pending_recruitment_from_data) < 1:
                        self.save_pending_recruitment()
                        break
                    else:
                        item = pending_recruitment_from_data.pop()

                sleep_time = item["create_at"].timestamp() + 30 - datetime_now.timestamp()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

    @interaction.command(name="구인", description="배틀그라운드를 함께할 플레이어를 모집해보세요!")
    async def recruitment(self, ctx: interaction.ApplicationContext):
        if ctx.guild is None:
            await ctx.send(comment_parser.get("Recruitment", "dm_channel"), hidden=True)
            return
        if self.has_recruitment_channel and ctx.channel.id not in self.recruitment_channel:
            await ctx.send(comment_parser.get("Recruitment", "no_recruitment"), hidden=True)
            return

        author: discord.Member = ctx.author
        user_voice_state: discord.VoiceState = ctx.author.voice

        if user_voice_state is None:
            await self.entrance_voice_channel(ctx)
            return
        voice_channel: discord.VoiceChannel = user_voice_state.channel
        channel_info_comment = self.voice_channel_formatter(
            comment_parser.get("Recruitment", "modal_information_comment"), voice_channel
        )
        await ctx.modal(
            custom_id=f"recruitment_{ctx.channel.id}_{author.id}_{voice_channel.id}",
            title=comment_parser.get("Recruitment", "modal_title"),
            components=[
                interaction.ActionRow(components=[
                    interaction.TextInput(
                        custom_id="information-nu1",
                        style=1,
                        label=comment_parser.get("Recruitment", "modal_information_title"),
                        placeholder=channel_info_comment,
                        value=channel_info_comment,
                        required=False
                    )
                ]), interaction.ActionRow(components=[
                    interaction.TextInput(
                        custom_id="comment",
                        style=2,
                        label=comment_parser.get("Recruitment", "modal_description_title"),
                        placeholder=comment_parser.get("Recruitment", "modal_description_placeholder"),
                        required=True
                    )
                ])
            ]
        )

    @interaction.listener()
    async def on_modal(self, ctx: interaction.ModalContext):
        if not ctx.custom_id.startswith("recruitment"):
            return

        if ctx.author.voice is None:
            await self.entrance_voice_channel(ctx)
            return
        voice_channel: discord.VoiceChannel = ctx.author.voice.channel
        comment_components = [x for x in ctx.components if x.custom_id == "comment"]
        if len(comment_components) > 0:
            comment = comment_components[0].value
        else:
            # No comment will happen
            comment = "설명이 없습니다."

        embed = discord.Embed(
            title=comment_parser.get("Recruitment", "embed_title"),
            description=self.author_formatter(comment_parser.get("Recruitment", "embed_description"), ctx.author)
        )
        category = voice_channel.category
        if category is not None:
            embed.add_field(name="카테고리", value=category.name, inline=False)
        embed.add_field(name="채널명", value=voice_channel.mention, inline=True)
        embed.add_field(
            name="멤버",
            value=self.voice_channel_member_count_formatter(
                comment_parser.get("Recruitment", "embed_member_count"),
                voice_channel
            ),
            inline=True
        )
        embed.add_field(name="설명", value=comment, inline=False)
        message = await ctx.send(embed=embed, components=[
            interaction.ActionRow(components=[
                interaction.Button(
                    style=5,
                    emoji=discord.PartialEmoji(name="\U0001F3A7"),
                    label=comment_parser.get("Recruitment", "button"),
                    url=voice_channel.jump_url
                )
            ])
        ])
        self.pending_recruitment[voice_channel.id] = {
            "requester": ctx.author,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "message": message,
            "origin_message": message,
            "created_at": message.created_at
        }
        self.save_pending_recruitment()

        await asyncio.sleep(
            parser.getint("DelayDelete", "pending_recruitment")
        )
        await message.delete()
        self.pending_recruitment.pop(voice_channel.id)
        self.save_pending_recruitment()
        return

    @interaction.listener()
    async def on_voice_state_update(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ):
        if before.channel == after.channel:
            return

        for channel in [before.channel, after.channel]:
            if channel is None:
                continue
            await self.voice_channel_update(channel)

    async def voice_channel_update(self, voice_channel: discord.VoiceChannel):
        if voice_channel.id not in self.pending_recruitment:
            return

        data = self.pending_recruitment[voice_channel.id]
        channel: discord.TextChannel = data["channel"]
        message: Union[interaction.Message, discord.PartialMessage] = data["message"]

        if "original_message" not in data.keys():
            try:
                # Important(Low Level)
                # Fetch_Message not implemented in discord-extension-interaction@feature/client-independence
                state: ConnectionState = getattr(self.client, "_connection")
                message_data = await state.http.get_message(channel.id, message.id)
                data["original_message"] = self.pending_recruitment[voice_channel.id]["original_message"] = (
                    interaction.Message(
                        state=state, channel=channel, data=message_data
                    )
                )
            except (discord.NotFound, discord.Forbidden):
                return

        original_message: interaction.Message = data["original_message"]
        components: List[interaction.ActionRow] = original_message.components
        if len(voice_channel.members) < 1 or len(voice_channel.members) >= voice_channel.user_limit != 0:
            # components[0].components[0].disabled = True
            self.pending_recruitment.pop(voice_channel.id)
            self.save_pending_recruitment()
            await message.delete()
            return

        for (index, value) in enumerate(original_message.embeds[0].fields):
            if value.name == "멤버":
                member_count_index = index
                break
        else:
            member_count_index = 2

        original_message.embeds[0].set_field_at(
            index=member_count_index,
            name="멤버",
            value=self.voice_channel_member_count_formatter("{current} / {limit}", voice_channel),
            inline=True
        )
        await message.edit(embeds=original_message.embeds, components=components)
        return

    @interaction.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.VoiceChannel) and channel.id in self.pending_recruitment:
            self.pending_recruitment.pop(channel.id)
            self.save_pending_recruitment()

    @staticmethod
    async def entrance_voice_channel(ctx: interaction.InteractionContext):
        comment = comment_parser.get("Recruitment", "entrance_voice_channel")
        await ctx.send(comment, hidden=True)
        return


def setup(client: interaction.Client):
    client.add_interaction_cog(Recruitment(client))
    
