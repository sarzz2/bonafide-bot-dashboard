from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.routers import auth, dashboard, tags
from app.db import Database

tags_metadata = []
app = FastAPI()

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Router apps setup
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(tags.router)


# database setup
@app.on_event("startup")
async def startup():
    database_instance = Database(
        user="sarzz", password="password", database="bonafidetest", host="localhost"
    )
    await database_instance.connect()
    app.state.db = database_instance
    # logger.info("Server Startup")


@app.on_event("shutdown")
async def shutdown_event():
    if not app.state.db:
        await app.state.db.close()
    # logger.info("Server Shutdown")
