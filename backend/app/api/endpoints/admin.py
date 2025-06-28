from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.types import StatusTypes, RoleTypes
from app.db.db import get_db
from app.db.models import User, PrintRequest
from app.db.schemas import UserResponse
from app.dependencies import require_admin_user, get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
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

@router.get("/print-requests/get-requests")
async def get_print_requests(
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(require_admin_user)
):
    if not (requests := (await db.execute(select(PrintRequest))).scalars().all()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Print requests not found",
        )
    return requests

@router.get("/print-requests/{print_request_id}")
async def get_specific_print_request(
        print_request_id: int,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(require_admin_user)
):

    if not (request := (await db.execute(select(PrintRequest).filter(PrintRequest.id == print_request_id))).scalars().first()):
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"Print request of id {print_request_id} not found",
        )
    return request

@router.patch("/print-requests/{print_request_id}/update-status-to-completed")
async def update_print_request(
        print_request_id: int,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(require_admin_user)
):

    if not (request := (await db.execute(select(PrintRequest).filter(PrintRequest.id == print_request_id))).scalars().first()):
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"Print request of id {print_request_id} not found",
        )

    request.status = StatusTypes.completed.value
    await db.commit()
    await db.refresh(request)

    return {"message": f"Status of print request {print_request_id} updated to completed."}

@router.post("/promote/{user_id}", status_code=status.HTTP_200_OK)
async def promote_user(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(require_admin_user)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")

    user.role = RoleTypes.admin.value
    await db.commit()
    return {"message": f"User {user_id} promoted to admin by {admin.username}"}