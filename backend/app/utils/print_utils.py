import uuid
import os
from fastapi import UploadFile, HTTPException
from typing import List, Tuple
import fitz
from app.utils.supabase_handler import upload_to_supabase

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpeg", ".jpg", ".png"}

async def calculate_total_pages_and_paths(files: List[UploadFile], username: str) -> Tuple[List[str], int]:
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
            with fitz.open(stream=await file.read(), filetype="pdf") as pdf:
                total_pages += pdf.page_count
        else:
            # Count 1 page per non-PDF file (or adjust logic as needed)
            total_pages += 1

    return uploaded_paths, total_pages
