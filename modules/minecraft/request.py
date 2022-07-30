import asyncio
import aiohttp
from typing import Optional

from modules.request import Requests as OriginRequests
from modules.model import Minecraft


class Requests(OriginRequests):
    def __init__(
            self,
            token: Optional[Minecraft] = None,
            loop: asyncio.AbstractEventLoop = None,
            session: aiohttp.ClientSession = None
    ):
        self.BASE1 = "https://api.minecraftservices.com"
        self.BASE2 = "https://api.mojang.com"
        self.BASE3 = "https://sessionserver.mojang.com"
        self.loop = loop

        self.token = None
        if token is not None:
            self.token = f"{token.token_type} {token.access_token}"
        super().__init__(loop=self.loop, session=session)

    async def requests(self, method: str, url: str, raise_on: bool = False, base_url: int = 1, **kwargs):
        if self.token is not None:
            headers = {
                "Authorization": self.token
            }

            if "headers" not in kwargs:
                kwargs["headers"] = headers
            else:
                kwargs["headers"].update(headers)

        url = getattr(self, f"BASE{base_url}") + url

        data = await super().requests(method, url, raise_on=raise_on, **kwargs)
        return data

    async def get(self, url: str, raise_on: bool = False, base_url: int = 1, **kwargs):
        return await self.requests(method="GET", url=url, raise_on=raise_on, base_url=base_url, **kwargs)

    async def post(self, url: str, raise_on: bool = False, base_url: int = 1, **kwargs):
        return await self.requests(method="POST", url=url, raise_on=raise_on, base_url=base_url, **kwargs)
