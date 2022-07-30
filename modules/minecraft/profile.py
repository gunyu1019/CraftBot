from typing import List, Optional
from pydantic import BaseModel


class Skins(BaseModel):
    id: str
    state: str
    variant: str
    url: str
    alias: Optional[str] = None


class Capes(BaseModel):
    id: str
    state: str
    url: str
    alias: Optional[str] = None


class Profile(BaseModel):
    id: str
    name: str
    skins: Optional[List[Skins]] = []
    capes: Optional[List[Capes]] = []
