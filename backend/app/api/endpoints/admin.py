from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.core.types import StatusTypes, RoleTypes
from app.db.db import get_db
from app.db.models import User, PrintRequest, PrintPricing, Payment
from app.db.schemas import UserResponse, PaymentResponse
from app.dependencies import require_admin_user, get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


@router.get("/get-users/", response_model=list[UserResponse])
async  def get_users(
        db: AsyncSession = Depends(get_db),
        current_user = Depends(get_current_user)
):
    if not (users := (await db.execute(select(User).filter(
        User.role == RoleTypes.user.value,
    ))).scalars().all()):
        raise HTTPException(status_code=404, detail="User not found")

    return users

@router.get("/get-user/{user_id}/", response_model=UserResponse)
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

@router.get("/print-requests/get-requests/")
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

@router.get("/print-requests/{print_request_id}/")
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

@router.patch("/print-requests/{print_request_id}/update-status-to-completed/")
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

@router.post("/promote/{user_id}/", status_code=status.HTTP_200_OK)
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

@router.patch("/demote/{user_id}/", status_code=status.HTTP_200_OK)
async def demote_user(
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(require_admin_user)
):
    if not ( user := (await db.execute(select(User).filter(User.id == admin.id))).scalars().first()):
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    user.role = RoleTypes.user.value
    await db.commit()
    return {"message": f"{user.username} demoted by {admin.username}"}


@router.post("/update-price/")
async def update_price(
        body: dict,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(require_admin_user)
):
    if not body:
            raise HTTPException(status_code=400, detail="Request body cannot be empty.")

    updated_items = []

    for key, new_value in body.items():
        result = (await db.execute(select(PrintPricing).where(PrintPricing.key == key))).scalars().first()

        if result:
            result.value = new_value
            updated_items.append({key: new_value})
        else:
            new_price = PrintPricing(key=key, value=new_value)      #add new if not exists
            db.add(new_price)
            updated_items.append({key: new_value})
    await db.commit()

    return {
        "message": "Pricing updated successfully.",
        "updated": updated_items
    }

@router.get("/payments/", response_model=list[PaymentResponse])
async def get_all_payments(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin_user)
):
    if not (payments := (await db.execute(select(Payment))).scalars().all()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payments not found",
        )
    return payments

@router.get("/payments/{payment_id}/", response_model=PaymentResponse)
async def get_payment_by_id(
        payment_id: int,
        db: AsyncSession = Depends(get_db),
        admin: User = Depends(require_admin_user)
):
    if not (payment := (await db.execute(select(Payment).filter(Payment.id == payment_id))).scalars().first()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment

@router.get("/payments/by-username/{username}/", response_model=PaymentResponse)
async def get_payments_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin_user)
):
    payments = (await db.execute(
        select(Payment)
        .join(Payment.print_request)
        .join(PrintRequest.user)
        .filter(User.username.ilike(f"%{username}%")) #for non case sensitive
        .options(joinedload(Payment.print_request).joinedload(PrintRequest.user))
    )).scalars().all()

    if not payments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No payments found for username: {username}",
        )

    return payments