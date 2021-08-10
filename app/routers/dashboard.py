from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from app.schemas.dashboard import GuildPreview, Cogs
from app.routers.auth import discord

router = APIRouter()


@router.get(
    "/dashboard",
    dependencies=[Depends(discord.requires_authorization)],
    response_model=List[GuildPreview],
)
async def dashboard(request: Request):
    """Show the guilds in which bot is there and the user is admin"""
    bot = await request.app.state.db.fetch_rows("SELECT * FROM guild")
    guilds = await discord.guilds(request)
    data = []

    for i in range(len(bot)):
        for j in range(len(guilds)):
            if int(bot[i].get("guild_id")) == int(guilds[j].id):
                if guilds[j].permissions & 8 == 8:
                    data.append(guilds[j])

    return data


@router.get(
    "/dashboard/{guild_id}",
    dependencies=[Depends(discord.requires_authorization)],
    response_model=List[Cogs],
)
async def dashboard_guild(request: Request, guild_id: int):
    """Show all the info of the guild to admin user"""
    guilds = await discord.guilds(request)
    for i in range(len(guilds)):
        if guild_id == int(guilds[i].id):
            if guilds[i].permissions & 8 == 8:
                cogs = await request.app.state.db.fetch_rows(
                    "SELECT * FROM cog_check WHERE guild_id = $1", guild_id
                )
                return cogs
            raise HTTPException(status_code=403, detail="Missing Permissions.")

    raise HTTPException(status_code=404, detail="Invalid ID/Bot not in server.")


@router.patch(
    "/update_cog/{guild_id}/{cog_name}",
    dependencies=[Depends(discord.requires_authorization)],
)
async def update_cog(request: Request, guild_id: int, cog_name: str, enabled: bool):
    """Enable or disable a cog"""
    guilds = await discord.guilds(request)
    for i in range(len(guilds)):
        if guild_id == int(guilds[i].id):
            if guilds[i].permissions & 8 == 8:
                await request.app.state.db.execute(
                    "UPDATE cog_check SET enabled = $3 WHERE guild_id = $1 AND cog_name = $2",
                    int(guild_id),
                    cog_name,
                    enabled,
                )
                return JSONResponse(content={cog_name: enabled})
            raise HTTPException(status_code=403, detail="Missing Permission")
    raise HTTPException(status_code=404, detail="Invalid ID/Bot not in server.")
