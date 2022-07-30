from config.config import get_config
from typing import NamedTuple


class Token(NamedTuple):
    token: str


parser = get_config()
token = Token(
    token=parser.get('DEFAULT', 'token'),
)
