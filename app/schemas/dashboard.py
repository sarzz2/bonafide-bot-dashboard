from typing import Optional, List

from pydantic import BaseModel


class Role(BaseModel):
    id: int
    name: str
    color: int
    position: int
    permissions: int
    managed: bool
    mentionable: bool


class GuildPreview(BaseModel):
    id: str = None
    name: str
    icon: Optional[str]
    owner: bool
    permissions: int
    features: List[str]


class Guild(GuildPreview):
    owner_id: Optional[int]
    verification_level: Optional[int]
    default_message_notifications: Optional[int]
    roles: Optional[List[Role]]


class Cogs(BaseModel):
    guild_id: int
    cog_name: str
    enabled: bool
