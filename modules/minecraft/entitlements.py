from typing import List
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    signature: str


class Entitlements(BaseModel):
    items: List[Item]
    signature: str
    keyId: str
