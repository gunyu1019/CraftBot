from typing import Union, Optional, Dict, Any


class AccessToken:
    def __init__(
            self,
            access_token: str,
            token_type: str,
            expires_in: int,
            scope: str,
            refresh_token: str = None,
            user_id: str = None,
            foci: Optional[str] = None,
            **_
    ):
        self.scope = scope.split()
        self.token = access_token
        self.type = token_type
        self.expires = expires_in
        self.refresh_token = refresh_token
        self.user_id = user_id
        self.foci = foci

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]):
        if 'token_type' not in payload:
            payload['token_type'] = "Bearer"
        if 'expires_in' not in payload:
            payload['expires_in'] = 0
        if 'scope' not in payload:
            payload['scope'] = ''
        return cls(**payload)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "access_token": self.token,
            "token_type": self.type,
            "scope": " ".join(self.scope),
            "expires_in": self.expires
        }
        if self.refresh_token is not None:
            result['refresh_token'] = self.refresh_token
        if self.user_id is not None:
            result['user_id'] = self.user_id
        if self.foci is not None:
            result['foci'] = self.foci
        return result


class XboxLive:
    def __init__(self, payload: Dict[str, Any]):
        self._issue_instant = payload.get('IssueInstant')
        self._not_after = payload.get('NotAfter')
        self.token = payload.get('Token')

        display_claims = payload.get('DisplayClaims', {})
        xui = display_claims.get('xui', [{}])[0]
        self.user_hash = xui.get('uhs')


class Minecraft:
    def __init__(self, payload: Dict[str, Any]):
        self.access_token = payload['access_token']
        self.username = payload['username']
        self.roles = payload.get('roles', [])
        self.token_type = payload.get('token_type', 'Bearer')
        self.expires_in = payload.get('expires_in', 0)


class Profile:
    __table_name__ = "profile"

    def __init__(self, payload: Dict[str, Any]):
        self.author_id = payload['author_id']
        self.refresh_token = payload['refresh_token']
        self.uuid = payload['minecraft_uuid']
        self.nickname = payload.get('player_nickname')

        self.representative = payload.get('representative', False)
        self.entitlements_java = payload.get('entitlements_minecraft_java_ed', False)
        self.entitlements_bedrock = payload.get('entitlements_minecraft_bedrock_ed', False)
        self.private_profile = payload.get('private_profile', False)
        self.private_nickname_history = payload.get('private_nickname_history', False)
