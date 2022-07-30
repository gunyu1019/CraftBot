import json
from datetime import datetime

try:
    import orjson
except ModuleNotFoundError:
    HAS_ORJSON = False
else:
    HAS_ORJSON = True

if HAS_ORJSON:
    from_json = orjson.loads
    to_dump = orjson.dumps
else:
    from_json = json.loads
    to_dump = json.dumps


class Pointer:
    def __init__(self):
        self._pointer_value = []

    def _add_pointer(self, value) -> int:
        self._pointer_value.append(value)
        return len(self._pointer_value) - 1

    def _get_pointer(self, position: int) -> str:
        return self._pointer_value.pop(position)
