import aiohttp
from typing import List, Tuple, Optional
from urllib.parse import urlencode

from modules.model import *
from modules.errors import *
from utils.utils import Pointer, to_dump


BASE = "https://login.live.com"


class Microsoft(Pointer):
    def __init__(
            self,
            client_id: str,
            client_secret: str
    ):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret

    def add_parameter(
            self,
            position: int,
            key: str,
            value: str,
            ended: bool = False
    ) -> None:
        self._pointer_value[position] += f"{key}={value}"
        if not ended:
            self._pointer_value[position] += "&"

    def authorize(
            self,
            redirect_uri: str,
            scope: List[str],
            response_type: str = "code",
            state: Optional[str] = None
    ) -> str:
        _scope = "%20".join(scope)
        _url = BASE + "/oauth20_authorize.srf?"
        position = self._add_pointer(_url)

        self.add_parameter(position, "client_id", self.client_id)
        self.add_parameter(position, "redirect_uri", redirect_uri)
        self.add_parameter(position, "response_type", response_type)
        if state is not None:
            self.add_parameter(position, "state", state)
        self.add_parameter(position, "scope", _scope, ended=True)
        return self._get_pointer(position)

    def token(
            self,
            redirect_uri: str,
            code: str = None,
            refresh_token: str = None,
            grant_type: str = "authorization_code"
    ) -> Tuple[str, dict]:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": grant_type
        }
        if code is not None:
            data['code'] = code
        if refresh_token is not None:
            data['refresh_token'] = refresh_token
        return BASE + "/oauth20_token.srf", data

    async def generate_access_token(
            self,
            redirect_uri: str,
            code: str,
            refresh: bool = False,
            session: aiohttp.ClientSession = None
    ) -> AccessToken:
        if not refresh:
            url, data = self.token(code=code, redirect_uri=redirect_uri)
        else:
            url, data = self.token(refresh_token=code, redirect_uri=redirect_uri)

        single_session = False
        if session is None:
            single_session = True
            session = aiohttp.ClientSession()

        async with session.post(
            url=url,
            data=data,
            headers={
                "Accept": "application/x-www-form-urlencoded",
                "User-Agent": "yhs.kr (Minecraft OAuth)"
            }
        ) as response:
            result = await response.json()
            if response.status != 200:
                raise HttpException(response.status, result)
        if single_session:
            await session.close()
        return AccessToken.from_payload(result)

    @staticmethod
    async def authenticate_with_xbox_live(
            access_token: AccessToken,
            session: aiohttp.ClientSession = None
    ) -> XboxLive:
        single_session = False
        if session is None:
            single_session = True
            session = aiohttp.ClientSession()

        data = {
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": "d={0}".format(access_token.token)
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        }
        async with session.post(
            url="https://user.auth.xboxlive.com/user/authenticate",
            json=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "yhs.kr (Minecraft OAuth)"
            }
        ) as response:
            if response.status != 200:
                raise HttpException(response.status, {})
            result = await response.json()
        if single_session:
            await session.close()
        return XboxLive(result)

    @staticmethod
    async def authenticate_with_xsts(
            xbox_live_profile: XboxLive,
            session: aiohttp.ClientSession = None
    ) -> XboxLive:
        single_session = False
        if session is None:
            single_session = True
            session = aiohttp.ClientSession()

        data = {
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [
                    xbox_live_profile.token
                ]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        }
        async with session.post(
                url="https://xsts.auth.xboxlive.com/xsts/authorize",
                json=data,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "yhs.kr (Minecraft OAuth)"
                }
        ) as response:
            if response.status != 200:
                raise HttpException(response.status, {})
            result = await response.json()
        if single_session:
            await session.close()
        return XboxLive(result)


    @staticmethod
    async def authenticate_with_minecraft(
            xbox_live_profile: XboxLive,
            session: aiohttp.ClientSession = None
    ) -> Minecraft:
        single_session = False
        if session is None:
            single_session = True
            session = aiohttp.ClientSession()

        data = {
            "identityToken": "XBL3.0 x={0};{1}".format(xbox_live_profile.user_hash, xbox_live_profile.token)
        }
        async with session.request(
            method="POST",
            url="https://api.minecraftservices.com/authentication/login_with_xbox",
            json=data,
            headers={
                "Accept": "application/json",
                "User-Agent": "yhs.kr (Minecraft OAuth)"
            }
        ) as response:
            result = await response.json()
            if response.status != 200:
                raise HttpException(response.status, result)
        if single_session:
            await session.close()
        return Minecraft(result)
