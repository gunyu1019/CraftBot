import discord
import asyncio
import logging

from discord.ext import tasks
from discord.ext import interaction

log = logging.getLogger(__name__)


class PresenceTask:
    def __init__(self, bot: interaction.Client):
        self.client = bot
        self.client.add_setup_hook(self.setup_hook)

    async def setup_hook(self):
        self.presence.start()

    @tasks.loop(seconds=3)
    async def presence(self):
        shard = self.client.shard_count
        if shard is None:
            await self.client.change_presence(
                status=discord.Status.online,
                activity=discord.Game(f"활동중인 서버갯수: {len(self.client.guilds)}")
            )
        else:
            await self.client.change_presence(
                status=discord.Status.online,
                activity=discord.Game(f"활동중인 서버갯수: {len(self.client.guilds)}, 샤드갯수: {self.client.shard_count}")
            )
        await asyncio.sleep(3.0)

        await self.client.change_presence(
            status=discord.Status.online,
            activity=discord.Game("버그/피드백 등은 Developer Space 커뮤니티로 문의해주세요.")
        )
        await asyncio.sleep(3.0)

        await self.client.change_presence(
            status=discord.Status.online,
            activity=discord.Game("더 이상 접두어를 활용하여 사용할 수 없습니다 :(")
        )
        await asyncio.sleep(3.0)

    @presence.before_loop
    async def before_booting(self):
        await self.client.wait_until_ready()


def setup(client):
    client.add_interaction_cog(PresenceTask(client))
