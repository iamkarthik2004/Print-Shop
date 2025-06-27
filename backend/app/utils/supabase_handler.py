import os
from dotenv import load_dotenv
import supabase
from supabase import AsyncClient

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET')

async def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_API_KEY:
        raise ValueError("Missing Supabase credentials in .env")
    return await AsyncClient.create(SUPABASE_URL, SUPABASE_API_KEY)

async def upload_to_supabase(path: str,file):
    content = await file.read()
    client = await get_supabase_client()
    response = await client.storage.from_(SUPABASE_BUCKET).upload(
        path = path,
        file = content,
        file_options = {"content-type": file.content_type, "upsert": False}
    )
    print(f"[DEBUG] {response}")
    # if response.code != 200:
    #     raise Exception("Supabase upload failed (non-200 response)")

    signed_url_response = await client.storage.from_(SUPABASE_BUCKET).create_signed_url(path, expires_in=604800)        # Generate signed URL ( for 1 week)

    if signed_url_response.get("signedURL"):
        return signed_url_response['signedURL']
    else:
        raise Exception("Signed URL generation failed")

async def remove_from_supabase(path: str):
    client = await get_supabase_client()
    await client.storage.from_(SUPABASE_BUCKET).remove([path])