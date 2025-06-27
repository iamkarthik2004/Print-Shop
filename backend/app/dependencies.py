from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.types import RoleTypes
from app.db.db import get_db
from app.db.models import User
from app.utils.jwt_handler import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        user_id = payload.get("id")
        role = payload.get("role")
        if not username or not user_id or not role:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return {
        "id": user_id,
        "username": username,
        "role": role,
    }

async def require_admin_user(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> User:
    print("[DEBUG] Current user:", current_user)
    admin = (await db.execute(
        select(User).filter(
            User.id == current_user["id"],
            User.role == RoleTypes.admin.value
        )
    )).scalars().first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is unauthorized"
        )
    return admin


async def user_exists(
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
) -> User:
    if not ( user := (await db.execute(select(User).filter(
        User.id == current_user["id"]
    ))).scalars().first()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{current_user} not found"
        )
    return user


