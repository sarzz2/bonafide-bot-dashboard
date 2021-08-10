from fastapi import APIRouter, Depends, Request, HTTPException

from app.routers.auth import discord

router = APIRouter()


@router.get(
    "/tags/{guild_id}",
    dependencies=[Depends(discord.requires_authorization)],
)
async def tags(request: Request, guild_id: int):
    """List all tags in the guild"""
    guilds = await discord.guilds(request)
    user = await discord.user(request)
    for i in range(len(guilds)):
        if guild_id == int(guilds[i].id):
            print(guilds[i])
            tag = await request.app.state.db.fetch_rows(
                "SELECT * FROM tag WHERE guild_id = $1", guild_id
            )
            return tag, user
    raise HTTPException(status_code=404, detail="Invalid ID/Bot not in server.")
