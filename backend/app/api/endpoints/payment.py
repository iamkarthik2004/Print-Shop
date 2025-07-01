from datetime import datetime, timezone

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_db
from app.db.models import User, Payment, PrintRequest
from app.dependencies import get_current_user
from app.utils.pdf_generator import generate_payment_receipt_pdf
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(
    prefix="/payment",
    tags=["payment"]
)

@router.post("/{payment_id}")
async def simulate_successful_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
):
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(404, detail="Payment not found")

    if payment.paid_at:
        return {"message": "Payment already completed."}

    payment.paid_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "message": f"Payment #{payment_id} marked as paid.",
        "paid_at": payment.paid_at.isoformat()
    }


@router.get("/payments/{payment_id}/receipt")
async def download_payment_receipt(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user)
):
    if not (payment := await db.get(Payment, payment_id)):
        raise HTTPException(status_code=404, detail="Payment not found")

    print_request = await db.get(PrintRequest, payment.print_request_id)

    if not ( user := await db.get(User, print_request.user_id) if print_request else None):
        raise HTTPException(status_code=404, detail="User for payment not found")

    pdf = generate_payment_receipt_pdf(
        username=user.username,
        amount=float(payment.amount),
        reference_id=str(payment.id)
    )

    return StreamingResponse(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=receipt_{payment_id}.pdf"
    })
