import logging

import discord
from discord.ext import commands
from discord.ext import interaction

from config.config import get_config

logger = logging.getLogger(__name__)
logger_command = logging.getLogger(__name__ + ".command")
logger_guild = logging.getLogger(__name__ + ".guild")
parser = get_config()


class Server:
    def __init__(self, bot):
        self.bot = bot

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

    @interaction.command(name="서버", description="마인크래프트 서버 정보를 불러옵니다.")
    @interaction.option(name="주소", description="서버 주소가 입력됩니다.")
    async def server(self, ctx, address: str):
        return


async def setup(client):
    client.add_icog(Server(client))
