from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, Depends, APIRouter
from fastapi.responses import RedirectResponse
from typing import Optional, List
from dotenv import load_dotenv

from app.schemas.auth import User, Guild, GuildPreview
from aiocache import cached
import aiohttp
import os

router = APIRouter()

load_dotenv()

DISCORD_URL = "https://discord.com"
DISCORD_API_URL = f"{DISCORD_URL}/api/v8"
DISCORD_OAUTH_URL = f"{DISCORD_URL}/api/oauth2"
DISCORD_TOKEN_URL = f"{DISCORD_OAUTH_URL}/token"
DISCORD_OAUTH_AUTHENTICATION_URL = f"{DISCORD_OAUTH_URL}/authorize"


# Exceptions
class Unauthorized(Exception):
    """A Exception raised when user is not authorized."""


class InvalidRequest(Exception):
    """A Exception raised when a Request is not Valid"""


class RateLimited(Exception):
    """A Exception raised when a Request is not Valid"""

    def __init__(self, json, headers):
        self.json = json
        self.headers = headers
        self.message = json["message"]
        self.retry_after = json["retry_after"]
        super().__init__(self.message)


class ScopeMissing(Exception):
    scope: str

    def __init__(self, scope: str):
        self.scope = scope
        super().__init__(self.scope)


class DiscordOAuthClient:
    """Client for Discord Oauth2.
    Parameters
    ----------
    client_id:
        Discord application client ID.
    client_secret:
        Discord application client secret.
    redirect_uri:
        Discord application redirect URI.
    """

    def __init__(self, client_id, client_secret, redirect_uri, scopes=("identify",)):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = "%20".join(scope for scope in scopes)

    @property
    def oauth_login_url(self):
        """
        Returns a Discord Login URL
        """
        client_id = f"client_id={self.client_id}"
        redirect_uri = f"redirect_uri={self.redirect_uri}"
        scopes = f"scope={self.scopes}"
        response_type = "response_type=code"
        return f"{DISCORD_OAUTH_AUTHENTICATION_URL}?{client_id}&{redirect_uri}&{scopes}&{response_type}"

    @cached(ttl=550)
    async def request(self, route, token, method="GET"):
        headers = {"Authorization": f"Bearer {token}"}
        resp = None
        if method == "GET":
            async with aiohttp.ClientSession() as session:
                resp = await session.get(f"{DISCORD_API_URL}{route}", headers=headers)
                data = await resp.json()
        if method == "POST":
            async with aiohttp.ClientSession() as session:
                resp = await session.post(f"{DISCORD_API_URL}{route}", headers=headers)
                data = await resp.json()
        if resp.status == 401:
            raise Unauthorized
        if resp.status == 429:
            raise RateLimited(data, resp.headers)
        return data

    async def get_access_token(self, code: str):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(DISCORD_TOKEN_URL, data=payload) as resp:
                resp = await resp.json()
                return resp.get("access_token"), resp.get("refresh_token")

    async def refresh_access_token(self, refresh_token: str):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(DISCORD_TOKEN_URL, data=payload) as resp:
                resp = await resp.json()
                return resp.get("access_token"), resp.get("refresh_token")

    async def user(self, request: Request):
        if "identify" not in self.scopes:
            raise ScopeMissing("identify")
        route = "/users/@me"
        token = self.get_token(request)
        return User(**(await self.request(route, token)))

    async def guilds(self, request: Request) -> List[GuildPreview]:
        if "guilds" not in self.scopes:
            raise ScopeMissing("guilds")
        route = "/users/@me/guilds"
        token = self.get_token(request)
        return [Guild(**guild) for guild in await self.request(route, token)]

    def get_token(self, request: Request):
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            raise Unauthorized
        authorization_header = authorization_header.split(" ")
        if not authorization_header[0] == "Bearer" or len(authorization_header) > 2:
            raise Unauthorized

        token = authorization_header[1]
        return token

    async def isAuthenticated(self, token: str):
        route = "/oauth2/@me"
        try:
            await self.request(route, token)
            return True
        except Unauthorized:
            return False

    async def requires_authorization(
        self, bearer: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
    ):
        if not await self.isAuthenticated(bearer.credentials):
            raise Unauthorized


discord = DiscordOAuthClient(
    os.getenv("CLIENT_ID"),
    os.getenv("CLIENT_SECRET"),
    "http://127.0.0.1:8000/callback/",
    ("identify", "guilds", "email"),
)


@router.get("/login")
async def login():
    return RedirectResponse(discord.oauth_login_url)


@router.get("/callback")
async def callback(code: str):
    token, refresh_token = await discord.get_access_token(code)
    return {"access_token": token, "refresh_token": refresh_token}


@router.get(
    "/authenticated",
    dependencies=[Depends(discord.requires_authorization)],
    response_model=bool,
)
async def isAuthenticated(token: str = Depends(discord.get_token)):
    try:
        auth = await discord.isAuthenticated(token)
        return auth
    except Unauthorized:
        return False


@router.get(
    "/user", dependencies=[Depends(discord.requires_authorization)], response_model=User
)
async def get_user(user: User = Depends(discord.user)):
    return user


@router.get(
    "/guilds",
    dependencies=[Depends(discord.requires_authorization)],
    response_model=List[GuildPreview],
)
async def get_guilds(guilds: List = Depends(discord.guilds)):
    return guilds
