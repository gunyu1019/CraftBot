import asyncio
import aiohttp
from typing import List

from .entitlements import Entitlements
from .errors import *
from .profile import Profile
from .profile_with_uuid import ProfileWithUUID
from .nickname_history import NicknameHistory
from .request import Requests
from ..model import Minecraft


class Client:
    def __init__(
            self,
            token: Minecraft = None,
            loop: asyncio.AbstractEventLoop = None,
            session: aiohttp.ClientSession = None
    ):
        self.loop = loop
        self.requests = Requests(token, loop, session)
        self.token = token

    async def entitlements(self) -> Entitlements:
        if self.token is None:
            raise TokenRequired()
        response = await self.requests.get(
            "/entitlements/mcstore", raise_on=True
        )
        return Entitlements(**response.data)

    async def profile(self) -> Profile:
        if self.token is None:
            raise TokenRequired()
        response = await self.requests.get(
            "/minecraft/profile", raise_on=True
        )
        return Profile(**response.data)

    async def profile_history(self, uuid: str) -> List[NicknameHistory]:
        response = await self.requests.get(
            "/user/profiles/{0}/names".format(uuid), raise_on=True, base_url=2
        )
        return [NicknameHistory(x) for x in response.data]

    async def profile_uuid(self, uuid: str) -> ProfileWithUUID:
        response = await self.requests.get(
            "/session/minecraft/profile/{0}".format(uuid), raise_on=True, base_url=3
        )
        return ProfileWithUUID(response.data)

    async def profile_nickname(self, nickname: str) -> Profile:
        response = await self.requests.get(
            "/users/profiles/minecraft/{0}".format(nickname), raise_on=True, base_url=2
        )
        return Profile(**response.data)
