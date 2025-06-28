from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.functions import user

from app.core.types import RoleTypes
from app.db.db import get_db
from app.db.models import User
from app.db.schemas import UserResponse
from app.dependencies import user_exists

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.patch("/update-user")
async def update_user(
        body: dict,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(user_exists)
):

    current_user.username = body.get("username",current_user.username)
    current_user.semester = body.get("semester",current_user.semester)
    current_user.department = body.get("department",current_user.department)
    current_user.year = body.get("year",current_user.year)
    await db.commit()
    await db.refresh(current_user)
    return {"message": f"User with user id {current_user.id} updated successfully"}



