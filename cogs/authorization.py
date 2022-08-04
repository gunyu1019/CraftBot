import logging
import random
import string

import aiohttp

import discord
from discord.ext import interaction

from config.config import get_config
from modules import minecraft
from modules.errors import HttpException
from modules.microsoft import Microsoft, AccessToken
from utils.database import connect_database

logger = logging.getLogger(__name__)
parser = get_config()
scope = parser.get("microsoft-oauth2", "scope").split()


class Authorization:
    def __init__(self, bot):
        self.bot = bot
        self.client = Microsoft(
            client_id=parser.get("microsoft-oauth2", "client_id"),
            client_secret=parser.get("microsoft-oauth2", "client_secret")
        )

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.generated_state_key = []

    def generate_state_key(self) -> str:
        state_key = ""
        for _ in range(8):
            state_key += random.choice(string.ascii_lowercase)

        if state_key in self.generated_state_key:
            return self.generate_state_key()
        return state_key

    @staticmethod
    def own_to_string(value: bool) -> str:
        if value:
            return "\U00002705 보유"
        return "\U0000274C 미보유"

    @interaction.command(name="가입", description="Microsoft 계정을 디스코드와 연결합니다.")
    async def authorization(self, ctx: interaction.ApplicationContext):
        state = self.generate_state_key()
        embed = discord.Embed(
            description="Minecraft를 CraftBot과 연결하기 위해서는 아래의 로그인이 필요합니다.\n"
                        "아래의 버튼을 눌러 XBOX 로그인을 진행해주세요.\n\n"
                        "* 로그인을 마친 경우 [통합 이용약관](https://yhs.kr/term)에 동의하는 것으로 간주합니다.\n"
                        "* Microsoft 계정에 마인크래프트 자바에디션을 보유하고 있어야 합니다.",
            color=self.color
        )
        embed.add_field(name="로그인 상태", value="<a:indicator:1001881861888409600> 대기 중", inline=True)
        embed.add_field(name="계정 인증 상태", value="<a:indicator:1001881861888409600> 대기 중", inline=True)
        components = interaction.ActionRow(components=[
            interaction.Button(
                style=5,
                url=self.client.authorize(
                    redirect_uri="https://localhost:3201/session/callback",
                    scope=scope,
                    state=state,
                ),
                emoji=discord.PartialEmoji(id=718482204035907586, name="XBOX"),
                label="로그인"
            )
        ])
        await ctx.send(embed=embed, components=[components], hidden=True)
        _, access_token = await self.bot.wait_for(
            "login_success",
            check=lambda process_state, _: process_state == state
        )
        access_token: AccessToken
        data = {
            "author_id": ctx.author.id,
            "refresh_token": access_token.refresh_token,
            "representative": True
        }
        components.components[0].disabled = True
        session = aiohttp.ClientSession(loop=self.bot.loop)
        embed.set_field_at(
            index=0,
            name=embed.fields[0].name,
            value="<a:indicator:1001881861888409600> XBOX 로그인 중",
            inline=embed.fields[0].inline
        )
        await ctx.edit(embed=embed, components=[components])

        try:
            xbl_token = await self.client.authenticate_with_xbox_live(access_token, session)
        except HttpException as _:
            embed.description += "\nXBOX 로그인에 실패했습니다. 다시 시도해주세요."
            embed.set_field_at(
                index=0,
                name=embed.fields[0].name,
                value="\U0000274C XBOX 로그인 실패",
                inline=embed.fields[0].inline
            )
            await ctx.edit(embed=embed, components=[components])
            return
        embed.set_field_at(
            index=0,
            name=embed.fields[0].name,
            value="<a:indicator:1001881861888409600> XSTS 토큰 조회",
            inline=embed.fields[0].inline
        )
        await ctx.edit(embed=embed, components=[components])

        try:
            xsts_token = await self.client.authenticate_with_xsts(xbl_token, session)
        except HttpException as error:
            embed.set_field_at(
                index=0,
                name=embed.fields[0].name,
                value="\U0000274C XSTS 토큰 조회 실패",
                inline=embed.fields[0].inline
            )
            if error.response_code == 401:
                xsts_error_code = error.data.get('XErr', 0)
                if xsts_error_code == 2148916233:
                    embed.description += "\nMicrosoft 계정에 XBOX 계정이 없습니다."
                    await ctx.edit(embed=embed, components=[components])
                    return
                elif xsts_error_code == 2148916235:
                    embed.description += "\nXBOX Live를 사용할 수 없거나, XBOX Live가 금지된 국가의 계정입니다."
                    await ctx.edit(embed=embed, components=[components])
                    return
                elif xsts_error_code == 2148916236 or xsts_error_code == 2148916237:
                    embed.description += "\nXBOX Live를 이용하기 위해서 성인 인증이 필요합니다."
                    await ctx.edit(embed=embed, components=[components])
                    return
                elif xsts_error_code == 2148916238 :
                    embed.description += "\nXBOX Live를 이용하기 위해서 부모(성인)의 계정을 가족에 추가해야합니다."
                    await ctx.edit(embed=embed, components=[components])
                    return
            embed.description += "\nXSTS(Xbox Live Security Token) 로그인에 실패했습니다. 다시 시도해주세요."
            embed.set_field_at(
                index=0,
                name=embed.fields[0].name,
                value="\U0000274C XSTS 토큰 조회 실패",
                inline=embed.fields[0].inline
            )
            await ctx.edit(embed=embed, components=[components])
            return
        await ctx.edit(embed=embed, components=[components])

        try:
            minecraft_token = await self.client.authenticate_with_minecraft(xsts_token, session)
        except HttpException as _:
            embed.description += "\n마인크래프트 로그인에 실패했습니다. 다시 시도해주세요."
            embed.set_field_at(
                index=0,
                name=embed.fields[0].name,
                value="\U0000274C 마인크래프트 토큰 조회 실패",
                inline=embed.fields[0].inline
            )
            await ctx.edit(embed=embed, components=[components])
            return
        embed.set_field_at(
            index=0,
            name=embed.fields[0].name,
            value="\U00002705 로그인 성공",
            inline=embed.fields[0].inline
        )
        embed.set_field_at(
            index=1,
            name=embed.fields[1].name,
            value="<a:indicator:1001881861888409600> 정품 소유 유/무 조회",
            inline=embed.fields[1].inline
        )
        # embed.description += "\n\n{player_name}님, 환영합니다!".format(player_name=minecraft_token.username)
        await ctx.edit(embed=embed, components=[components])

        client = minecraft.Client(token=minecraft_token, session=session)
        entitlements = await client.entitlements()
        owned_items = {
            "game_minecraft": False,
            "game_minecraft_bedrock": False
        }
        for item in entitlements.items:
            if item.name in owned_items:
                owned_items[item.name] = True

        data['entitlements_minecraft_java_ed'] = owned_items['game_minecraft']
        data['entitlements_minecraft_bedrock_ed'] = owned_items['game_minecraft_bedrock']
        if not owned_items['game_minecraft']:
            embed.description += f"\n\n마인크래프트 자바에디션 소유권을 찾을 수 없습니다."
            embed.set_field_at(
                index=1,
                name=embed.fields[1].name,
                value=f"\U0000274C 마인크래프트 자바에디션 미보유",
                inline=embed.fields[1].inline,
            )
            await ctx.edit(embed=embed, components=[components])
            return
        database = connect_database()
        embed.set_field_at(
            index=1,
            name=embed.fields[1].name,
            value=f"<a:indicator:1001881861888409600> 사용자 정보 조회",
            inline=embed.fields[1].inline
        )
        await ctx.edit(embed=embed, components=[components])
        profile = await client.profile()

        data['player_nickname'] = profile.name
        data['minecraft_uuid'] = profile.id
        data['private_profile'] = False
        data['private_nickname_history'] = True

        embed.description += f"\n\n{profile.name}({profile.id})님 환영합니다!"
        if database.is_exist("profile", key=profile.id, key_name="minecraft_uuid"):
            embed.description += f"\n이미 등록된 계정입니다."
            embed.set_field_at(
                index=1,
                name=embed.fields[1].name,
                value=f"\U0000274C 등록된 계정",
                inline=embed.fields[1].inline,
            )
            await ctx.edit(embed=embed, components=[components])
            database.close()
            return

        if database.is_exist("profile", key=ctx.author.id, key_name="author_id"):
            data['representative'] = False
        database.insert("profile", data)
        database.close(check_commit=True)

        embed.set_field_at(
            index=1,
            name=embed.fields[1].name,
            value=f"\U00002705 인증 성공",
            inline=embed.fields[1].inline,
        )
        await ctx.edit(embed=embed, components=[components])
        await session.close()
        return


async def setup(client):
    client.add_icog(Authorization(client))
