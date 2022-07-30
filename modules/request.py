import aiohttp
import asyncio

from typing import Type
from modules.errors import (
    NotFound,
    ServiceUnavailable,
    InternalServerError,
    BadRequest,
    TooManyRequests,
    Forbidden,
    MethodNotAllowed,
)


class Response:
    def __init__(self, status: int, **kwargs):
        self.status = status
        self.data = kwargs["data"]
        self.headers = kwargs["headers"]

        self.version = kwargs.get("version")
        self.content_type = kwargs.get("content_type") or self.headers.get(
            "Content-Type"
        )
        self.reason = kwargs.get("reason")


class Requests:
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        session: aiohttp.ClientSession = None,
        e400: Type[BadRequest] = None,
        e403: Type[Forbidden] = None,
        e404: Type[NotFound] = None,
        e405: Type[MethodNotAllowed] = None,
        e429: Type[TooManyRequests] = None,
        e500: Type[InternalServerError] = None,
        e503: Type[ServiceUnavailable] = None,
    ):
        self.loop = loop or asyncio.get_event_loop()
        self.session = session

        self.e400 = e400 or BadRequest
        self.e403 = e403 or Forbidden
        self.e404 = e404 or NotFound
        self.e405 = e405 or MethodNotAllowed
        self.e429 = e429 or TooManyRequests
        self.e500 = e500 or InternalServerError
        self.e503 = e503 or ServiceUnavailable

    @staticmethod
    async def check_content(resp):
        if resp.content_type.startswith("application/json"):
            return await resp.json()
        elif resp.content_type.startswith("image/"):
            return await resp.content.read()
        elif resp.content_type.startswith("text/html"):
            return await resp.text()
        else:
            return None

    async def requests(
        self, method: str, url: str, raise_on: bool = False, **kwargs
    ) -> Response:
        single_session = False
        session = self.session
        if session is None:
            single_session = True
            session = aiohttp.ClientSession(loop=self.loop)
        async with session.request(method, url, **kwargs) as resp:
            data = await self.check_content(resp)
            request_data = Response(
                status=resp.status,
                data=data,
                version=resp.version,
                content_type=resp.content_type,
                reason=resp.reason,
                headers=resp.headers,
            )

            if raise_on:
                if request_data.status == 400:
                    raise self.e400(resp.status, data)
                elif request_data.status == 403:
                    raise self.e403(resp.status, data)
                elif request_data.status == 404:
                    raise self.e404(resp.status, data)
                elif request_data.status == 405:
                    raise self.e405(resp.status, data)
                elif request_data.status == 429:
                    raise self.e429(resp.status, data)
                elif request_data.status == 500:
                    raise self.e500(resp.status, data)
                elif request_data.status == 503:
                    raise self.e503(resp.status, data)

        if single_session:
            await session.close()
        return request_data

    async def get(self, url: str, raise_on: bool = False, **kwargs):
        return await self.requests(method="GET", url=url, raise_on=raise_on, **kwargs)

    async def post(self, url: str, raise_on: bool = False, **kwargs):
        return await self.requests(method="POST", url=url, raise_on=raise_on, **kwargs)
