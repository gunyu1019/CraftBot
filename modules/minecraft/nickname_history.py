from datetime import datetime
from typing import Optional, Dict, Any


class NicknameHistory:
    def __init__(self, payload: Dict[str, Any]):
        self.name = payload['name']
        self._changed_at: int = payload.get('changedToAt')
        self.is_current = self._changed_at is None

    @property
    def changed_at(self) -> Optional[datetime]:
        if self._changed_at is None:
            return
        now = datetime.now().timestamp() - self._changed_at / 10000
        return datetime.fromtimestamp(now)
