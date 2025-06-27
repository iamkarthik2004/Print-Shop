from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.db import init_db
from app.api.endpoints import auth, request, admin, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
# Include routers
app.include_router(auth.router)
app.include_router(request.router)
app.include_router(admin.router)
app.include_router(user.router)
