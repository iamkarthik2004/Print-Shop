import uuid
import os
from fastapi import UploadFile, HTTPException
from typing import List, Tuple, Optional
import fitz
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from sqlalchemy.future import select
import re
from app.core.types import SidesTypes, OrientationTypes
from app.db.models import PrintPricing
from app.utils.supabase_handler import upload_to_supabase

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpeg", ".jpg", ".png"}

def parse_custom_pages(custom_pages: str, max_page: int) -> int:
    pages_set = set()

    for part in custom_pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            start = int(start)
            end = int(end)
            if start < 1 or end > max_page or start > end:
                raise ValueError(f"Invalid range: {start}-{end}")
            pages_set.update(range(start, end + 1))
        else:
            num = int(part)
            if num < 1 or num > max_page:
                raise ValueError(f"Page number out of range: {num}")
            pages_set.add(num)

    return len(pages_set)


async def calculate_total_pages_and_paths(
        files: List[UploadFile],
        username: str,
        custom_pages_map: Optional[str] = None
) -> Tuple[List[str], int]:
    uploaded_paths = []
    total_pages = 0

    for file in files:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")

        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"print-request/{username}/{unique_filename}"

        # Upload to Supabase
        uploaded_url = await upload_to_supabase(file_path, file)
        uploaded_paths.append(uploaded_url)

        if file_extension == ".pdf":
            file.file.seek(0)
            file_bytes = await file.read()
            with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
                max_page = pdf.page_count
                file_key = file.filename

                if custom_pages_map and file_key in custom_pages_map:
                    try:
                        page_count = parse_custom_pages(custom_pages_map[file_key], max_page)
                        total_pages += page_count
                    except ValueError as e:
                        raise HTTPException(status_code=400, detail=f"Custom page error: {str(e)}")
                else:
                    total_pages += max_page
        else:
            # Non-pdf treated as 1 page
            total_pages += 1

    return uploaded_paths, total_pages


async def calculate_total_cost(
        color: bool,
        sides: SidesTypes,
        orientation: OrientationTypes,
        pages: int,
        db: AsyncSession
) -> Decimal:
    keys = []
    if color:
        keys.append("color")
    else:
        keys.append("bw")
    keys.append(sides.lower())
    keys.append(orientation.lower())

    prices = (await db.execute(
        select(PrintPricing).where(PrintPricing.key.in_(keys))
    )).scalars().all()

    base_cost = sum(p.value for p in prices)
    total_cost = base_cost * Decimal(pages)
    return total_cost