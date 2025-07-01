# app/api/routes/request.py
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.dependencies import user_exists
from app.db.models import User, PrintRequest, PrintFiles, Payment
from app.core.types import OrientationTypes, SidesTypes, PaymentMethodTypes, PaymentStatusTypes
from app.utils.pdf_generator import generate_summary_pdf
from app.utils.print_utils import calculate_total_pages_and_paths, calculate_total_cost
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse


router = APIRouter(
    prefix="/request",
    tags=["request"]
)

@router.post("/print-requests", status_code=status.HTTP_201_CREATED)
async def create_print_request(
    color: bool = Form(...),
    sides: SidesTypes = Form(...),
    orientation: OrientationTypes = Form(...),
    custom_pages: str = Form(...),
    files: list[UploadFile] = File(...),
    payment_method: PaymentMethodTypes = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(user_exists)
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    try:
        file_paths, total_pages = await calculate_total_pages_and_paths(files, user.username, custom_pages)
        amount = await calculate_total_cost(color=color, sides=sides.value, orientation=orientation.value, pages=total_pages, db=db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload or page count failed: {str(e)}")

    new_request = PrintRequest(
        user_id=user.id,
        color=color,
        sides=sides,
        orientation=orientation,
        no_of_pages=total_pages,
        custom_pages=custom_pages,
        created_at=datetime.now(timezone.utc),
        files=[PrintFiles(file_path=url) for url in file_paths],
        payment_status=PaymentStatusTypes.pending.value
    )
    db.add(new_request)
    await db.flush()

    new_payment = Payment(
        amount=amount,
        print_request_id=new_request.id,
        payment_method=payment_method
    )
    db.add(new_payment)

    try:
        await db.commit()
        await db.refresh(new_request)
        await db.refresh(new_payment)
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"DB error: {str(e)}")

    redirect_url = f"/pay/{new_payment.id}"

    return {
        "message": "Print request created",
        "print_request_id": new_request.id,
        "payment_id": new_payment.id,
        "amount": float(amount),
        "payment_method": payment_method,
        "redirect_url": redirect_url
    }


@router.get("/print-requests/{id}/summary")
async def download_summary_pdf(
        id: int,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(user_exists)
):
    request = await db.get(PrintRequest, id)
    if not request or request.user_id != user.id:
        raise HTTPException(status_code=404, detail="Print request not found")

    pdf = generate_summary_pdf(
        username=user.username,
        custom_pages=request.custom_pages,
        total_pages=request.no_of_pages,
        color=request.color,
        sides=request.sides,
        orientation=request.orientation,
        amount=request.payment.amount if request.payment else 0,
        payment_method=request.payment.payment_method if request.payment else "N/A"
    )

    return StreamingResponse(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=summary_{id}.pdf"
    })
