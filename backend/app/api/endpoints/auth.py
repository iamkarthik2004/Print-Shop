# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.db import get_db
from app.db.schemas import UserCreate
from app.db.models import User
from app.core.security import hash_password, verify_password
from app.core.types import RoleTypes
from app.utils.jwt_handler import create_access_token
from app.dependencies import get_current_user

router = APIRouter(tags=["Authentication"], prefix="/auth")


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: UserCreate, db: AsyncSession = Depends(get_db)):
    user_exists = await db.execute(select(User).filter(User.username == body.username))
    if user_exists.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {body.username} already exists"
        )

    new_user = User(
        username=body.username,
        password=hash_password(body.password),
        semester=body.semester,
        department=body.department,
        year=body.year,
        role=RoleTypes.user.value
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": f"User {new_user.username} created"}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role, "id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/promote/{user_id}", status_code=status.HTTP_200_OK)
async def promote_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can promote users"
        )

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")

    user.role = RoleTypes.admin.value
    await db.commit()
    return {"message": f"User {user_id} promoted to admin by {current_user['username']}"}
