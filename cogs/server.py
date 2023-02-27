import logging
import socket
import os
import io
import base64
import mcstatus
import discord
from discord.ext import commands
from discord.ext import interaction
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel
from typing import Optional, List, Tuple
from socket import timeout

from config.config import get_config
from utils.directory import directory

logger = logging.getLogger(__name__)
logger_command = logging.getLogger(__name__ + ".command")
logger_guild = logging.getLogger(__name__ + ".guild")
parser = get_config()
font_location = os.path.join(directory, "assets", "font", "Minecraftia-Regular.ttf")


class ServerData(BaseModel):
    title: List[str]
    icon: Optional[str]
    version: str
    online_player: int
    max_player: int
    player_list: Optional[list]
    ping: float


class Server:
    def __init__(self, bot):
        self.bot = bot

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.server_title1_font = ImageFont.truetype(font_location, size=36)
        self.server_title2_font = ImageFont.truetype(font_location, size=30)
        self.server_player_list_font = ImageFont.truetype(font_location, size=24)

    @staticmethod
    def text(canvas: ImageDraw.ImageDraw, text: str, position: Tuple[int], font: ImageFont.ImageFont = None):
        _pos_x = position[0]
        for _text in text.split("§"):
            text_x, _ = canvas.textsize(text=text, font=font)
            _pos_x += text_x
        return canvas

    @interaction.command(name="서버", description="마인크래프트 서버 정보를 불러옵니다.")
    @interaction.option(name="주소", description="서버 주소가 입력됩니다.")
    @interaction.option(name="포트", description="서버 포트가 입력됩니다. (기본 값: 자바 에디션 25565, 베드락 에디션 19132)")
    @interaction.option(
        name="유형",
        description="자바 에디션 또는 베드락 에디션 중 하나를 선택해주세요. 기본 값은 자바 에디션입니다.",
        choices=[
            interaction.CommandOptionChoice(name="자바에디션", value="JavaEdition"),
            interaction.CommandOptionChoice(name="베드락에디션", value="BedrockEdition")
        ]
    )
    async def server(self, ctx, address: str, port: int = None, server_type: str = "JavaEdition"):
        await ctx.defer()
        if server_type == "JavaEdition":
            original_address = address
            if port is not None:
                address += ":{0}".format(port)
            lookup = await mcstatus.JavaServer.async_lookup(address)
            try:
                status = await lookup.async_status()
                data = ServerData(**{
                    "title": status.description.split('\n'),
                    "icon": status.favicon,
                    "version": status.version.name,
                    "online_player": status.players.online,
                    "max_player": status.players.max,
                    "player_list": status.players.sample,
                    "ping": status.latency
                })
            except socket.timeout:
                pass

            try:
                ping = await lookup.async_ping()
                data.ping = ping
            except (socket.timeout, IOError):
                pass

            canvas_height = 374
            if len(data.player_list) > 0:
                _dummy_canvas = Image.new('RGBA', (784, 784))
                _dummy_canvas_draw = ImageDraw.Draw(_dummy_canvas)
                _, player_list_height = _dummy_canvas_draw.textsize(
                    "\n".join([x.name for x in data.player_list]),
                    font=self.player_list_font
                )
                canvas_height += 89 + player_list_height
                _dummy_canvas.close()

            canvas = Image.new('RGBA', (784, canvas_height))
            canvas_draw = ImageDraw.Draw(canvas)
            if data.icon is not None:
                pre_icon = data.icon.replace("data:image/png;base64,", "")
                icon: Image.Image = Image.open(
                    io.BytesIO(
                        base64.b64decode(pre_icon + '=' * (-len(pre_icon) % 4))
                    )
                )
                icon = icon.resize((170, 170), resample=Image.Resampling.BOX)
                canvas.alpha_composite(icon, (30, 30))
            else:
                # _title_image_x, _title_image_y = canvas_draw.textsize()
                # canvas_draw.text()
                pass

            buffer = io.BytesIO()
            canvas.save(buffer, format="png")
            buffer.seek(0)

            embed = discord.Embed(color=self.color)
            embed.set_image(url="attachment://{0}_server.png".format(address))
            await ctx.send(
                embed=embed,
                file=discord.File(buffer, filename="{0}_server.png".format(address))
            )
            return
        elif server_type == "BedrockEdition":
            return

        return


def setup(client):
    client.add_interaction_cog(Server(client))


a = {
    'raw': {
        'description': {
            'text': '§a§l                    §a✿ §b§l수련낙원§a ✿\n§e     §f오늘은 수요일! §a[저녁 9시]§f 에 §4§n(핫타임 룰렛) §f을 시작합니다.'
        },
        'players': {
            'max': 500,
            'online': 51,
            'sample': [
                {'id': '19e6dd68-093f-4f08-8f0e-2c942cb8fe5a', 'name': ''},
                {'id': '547399ae-da18-4ff7-8bbc-73bd0808db73',
                 'name': '§c❀§d✾§b✾§e❀§5✿❁§e✾❀✿§6❁✾❀§b✿❁§2✾§c❀✿§9❁§e✾❀✿❁§a✾❀✿§4❁§c✾'},
                {'id': '49d750fa-001f-4c5d-baf1-15018e0f8751', 'name': ''},
                {'id': '96ee66a1-58f9-431c-b5ec-38cd4852915d', 'name': '§c   ✿ §7저희 세계는 마인팜 컨텐츠 기반의 서버예요. §c✿'},
                {'id': '5a4bd7df-bbc1-4730-9d2c-bc57f06c53d8', 'name': '     §6✿ §7나만의 섬에서 영역을 넓히고 성장하여 §6✿'},
                {'id': 'faace3a9-8a5d-4ee0-82ee-40ed9711ee09', 'name': '  §l  §e✿ §7더 많은 금전을 획득하고 부자의 생활을 §e✿'},
                {'id': 'be2b5e56-038d-46e3-8656-f35c9654f473', 'name': '     §a✿ §7꿈꿔 보세요! 함께 행복을 찾아 떠나요! §a✿'},
                {'id': 'df0da248-bcd1-423d-a294-a7245ef8f49d', 'name': ''},
                {'id': '74e09be7-38e7-4f86-a239-85124d8586a2',
                 'name': '§b✾§e❀§5✿❁§b✾❀✿§6❁✾❀§7✿❁§2✾§c❀✿§9❁§e✾❀✿❁§a✾❀✿§4❁§9✾§e✾§c❀§l'},
                {'id': 'f294572a-dee0-4ea9-8ef8-55f3d5742867', 'name': '        §a오늘의 신규유저: §f18 §c오늘의 복귀유저: §f없음'}
            ]
        },
        'version': {
            'name': 'Paper 1.12.2',
            'protocol': 340
        }
    }
}
