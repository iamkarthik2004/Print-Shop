# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from app.db.db import init_db
from app.api.endpoints import auth, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
# Include routers
app.include_router(auth.router)
app.include_router(user.router)
