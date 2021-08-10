from typing import List, Optional, Any
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


class User(BaseModel):
    id: str = None
    username: str
    discriminator: str
    avatar: str
    avatar_url: Optional[str]
    locale: str
    email: Optional[str]
    bot: Optional[bool]
    mfa_enabled: bool
    flags: int
    premium_type: Optional[int]
    public_flags: int

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.avatar_url = (
            f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        )
