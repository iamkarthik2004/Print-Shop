# app/api/routes/request.py
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.dependencies import user_exists
from app.db.models import User, PrintRequest, PrintFiles
from app.core.types import OrientationTypes, SidesTypes
from app.utils.print_utils import calculate_total_pages_and_paths
from datetime import datetime, timezone


router = APIRouter(
    prefix="/request",
    tags=["request"]
)

@router.post("/print-requests", status_code=status.HTTP_201_CREATED)
async def create_print_request(
    color: bool = Form(...),
    sides: SidesTypes = Form(...),
    orientation: OrientationTypes = Form(...),
    pages: str = Form(...),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(user_exists)
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    try:
        file_paths, total_pages = await calculate_total_pages_and_paths(files, user.username)
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
        custom_pages=pages,
        created_at=datetime.now(timezone.utc),
        files=[PrintFiles(file_path=url) for url in file_paths]
    )

    try:
        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)
    except Exception as e:
        raise HTTPException(500, f"DB error: {str(e)}")

    return {"message": f"Print request created for {user.username}"}
