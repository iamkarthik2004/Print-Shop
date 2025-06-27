# app/api/routes/user.py
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.db import get_db
from app.dependencies import get_current_user
from app.db.models import User, PrintRequest
from app.core.types import OrientationTypes, SidesTypes
from app.utils.supabase_handler import upload_to_supabase, remove_from_supabase
from datetime import datetime, timezone
import uuid
import os

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.post("/print-requests", status_code=status.HTTP_201_CREATED)
async def create_print_request(
    color: bool = Form(...),
    sides: SidesTypes = Form(...),
    orientation: OrientationTypes = Form(...),
    pages: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    username = current_user.get("username")
    user_id = current_user.get("id")
    if not username or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = (await db.execute(select(User).filter(User.username == username))).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"User {username} not found")

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in {".pdf", ".doc", ".docx", ".jpeg", ".jpg", ".png"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = f"print-request/{username}/{unique_filename}"

    try:
        new_file_path = await upload_to_supabase(file_path, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_request = PrintRequest(
        user_id=user_id,
        file_path=new_file_path,
        color=color,
        sides=sides,
        orientation=orientation,
        pages=pages,
        status="waiting",
        created_at=datetime.now(timezone.utc)
    )
    try:
        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)
    except Exception as e:
        await remove_from_supabase(file_path)
        raise HTTPException(500, f"DB error: {str(e)}")

    return {"message": f"Print request created for {username}"}
