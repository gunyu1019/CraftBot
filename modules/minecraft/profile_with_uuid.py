from base64 import b64decode
from typing import List, Optional, Dict, Any, Union

from .profile import Skins, Capes
from utils.utils import from_json


class ProfileWithUUID:
    def __init__(self, payload: Dict[str, Any]):
        self.id: str = payload['id']
        self.name: str = payload['name']
        self._properties: str = payload['properties']
        self.legacy: Optional[bool] = payload.get('legacy')

    @property
    def properties(self):
        return Properties(self._properties[0]['value'])

    @property
    def skin(self) -> Optional[Skins]:
        return self.properties.skin

    @property
    def cape(self) -> Optional[Capes]:
        return self.properties.cape


class Properties:
    def __init__(self, encoded_key: Union[str, bytes]):
        self._key = encoded_key
        self._payload = from_json(b64decode(self._key + "=="))

        self._timestamp = self._payload['timestamp']
        self._textures = self._payload['textures']

    @property
    def skin(self) -> Optional[Skins]:
        if "SKIN" not in self._textures:
            return
        variant = self._textures['SKIN'].get('metadata', {}).get("model", "CLASSIC")
        data = {
            "id": "",
            "state": "ACTIVE",
            "variant": variant,
            "url": self._textures['SKIN']["url"]
        }
        return Skins(**data)

    @property
    def cape(self) -> Optional[Capes]:
        if "CAPE" not in self._textures:
            return
        data = {
            "id": "",
            "state": "ACTIVE",
            "url": self._textures['CAPE']["url"]
        }
        return Capes(**data)
