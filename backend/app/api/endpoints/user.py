from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.functions import user

from app.core.types import RoleTypes
from app.db.db import get_db
from app.db.models import User
from app.db.schemas import UserResponse
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.get("/get-users", response_model=list[UserResponse])
async  def get_users(
        db: AsyncSession = Depends(get_db),
        current_user = Depends(get_current_user)
):
    if not (users := (await db.execute(select(User).filter(
        User.role == RoleTypes.user.value,
    ))).scalars().all()):
        raise HTTPException(status_code=404, detail="User not found")

    return users

@router.get("/get-user/{user_id}", response_model=UserResponse)
async def get_user_by_id(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user = Depends(get_current_user)
):
    if not (specific_user := (await db.execute(select(User).filter(
        User.id == user_id
    ))).scalars().first()):
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return specific_user

@router.patch("/update-user/{user_id}")
async def update_user(
        user_id: int,
        body: dict,
        db: AsyncSession = Depends(get_db),
        current_user = Depends(get_current_user)
):
    if not (specific_user := (await db.execute(select(User).filter(
        User.id == user_id
    ))).scalars().first()):
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    specific_user.username = body.get("username",specific_user.username)
    specific_user.semester = body.get("semester",specific_user.semester)
    specific_user.department = body.get("department",specific_user.department)
    specific_user.year = body.get("year",specific_user.year)
    await db.commit()
    await db.refresh(specific_user)
    return {"message": f"User with user id {user_id} updated successfully"}



