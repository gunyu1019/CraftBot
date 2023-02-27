import io
import logging
import aiohttp
import discord
from discord.ext import commands
from discord.ext import interaction
from typing import List, Optional
from PIL import Image, ImageDraw

from config.config import get_config
from modules.model import Profile as ProfileDatabaseModel
from modules.minecraft import Client as MinecraftClient
from modules.skin_render import SkinRender, Direction
from process.profile import ProfileProcess
from utils.database import connect_database

logger = logging.getLogger(__name__)
parser = get_config()


class Profile:
    def __init__(self, bot: interaction.Client):
        self.bot = bot

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

    @interaction.command(name="프로필", description="마인크래프트 등록된 프로필 정보를 불러옵니다.")
    @interaction.option(name="사용자", description="다른 사용자를 조회할 경우에 활용됩니다.")
    async def profile(self, ctx: interaction.ApplicationContext, author: discord.User = None):
        if author is None:
            author = ctx.author
        await ctx.defer()
        if author.id == self.bot.user.id:
            author = await self.bot.fetch_user(340373909339635725)
        elif author.bot:
            embed = discord.Embed(
                description="봇이 마인크래프트을 하고 있으면, 랭커가 되어 있을 것입니다.",
                color=self.warning_color
            )
            embed.set_author(
                name=f"{author.name}#{author.discriminator}",
                icon_url=author.display_avatar.url
            )
            await ctx.send(embed=embed)
            return

        database = connect_database()
        selected_player: Optional[List[ProfileDatabaseModel]] = database.query_all(
            table=ProfileDatabaseModel,
            key_name="author_id",
            key=author.id
        )
        if selected_player is None:
            embed = discord.Embed(
                description="해당 사용자는 CraftBot에 연동한 마인크래프트 계정이 없거나, 프로필 정보가 비공개 되어 있습니다.",
                color=self.warning_color
            )
            embed.set_author(
                name=f"{author.name}#{author.discriminator}",
                icon_url=author.display_avatar.url
            )
            await ctx.send(embed=embed)
            return
        representative_index = 0
        for index, player in enumerate(selected_player):
            if player:
                representative_index = index
                break
        database.close()

        client = ProfileProcess(ctx, self.bot, author, selected_player)
        await client.profile(representative_index)
        return

    @interaction.command(name="스킨", description="마인크래프트 스킨을 불러옵니다.")
    @interaction.option(name="닉네임", description="스킨을 조회할 닉네임을 입력합니다.")
    async def skin_profile(self, ctx: interaction.ApplicationContext, nickname: str):
        await ctx.defer()

        session = aiohttp.ClientSession()
        minecraft_client = MinecraftClient(loop=self.bot.loop, session=session)
        nickname_data = await minecraft_client.profile_nickname(nickname=nickname)

        embed = discord.Embed(color=self.color)
        embed.set_image(url="attachment://{0}_skin.png".format(nickname))
        embed.set_author(
            name=f"{nickname_data.name}님의 스킨",
            icon_url=ctx.author.display_avatar.url
        )
        skin_data = await SkinRender.from_uuid(uuid=nickname_data.id, session=session, scale=12)
        await session.close()

        front_skin_image = skin_data.portrait(direction=Direction.front)
        back_skin_image = skin_data.portrait(direction=Direction.back)

        canvas = Image.new('RGBA', (512, 512), (47, 49, 54))
        canvas_draw = ImageDraw.Draw(canvas)

        canvas_draw.text((32, 32), text=nickname, fill=(255, 255, 255), font=ProfileProcess.profile_player_name_font)
        canvas.alpha_composite(front_skin_image, (44, 98))
        canvas.alpha_composite(back_skin_image, (275, 98))

        buffer = io.BytesIO()
        canvas.save(buffer, format='png')
        buffer.seek(0)

        await ctx.send(
            embed=embed,
            file=discord.File(buffer, filename="{0}_skin.png".format(nickname))
        )
        return


def setup(client):
    client.add_interaction_cog(Profile(client))
