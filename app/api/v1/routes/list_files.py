from fastapi import APIRouter
from src.pipeline import list_uploaded_files
router = APIRouter()

@router.get("/list")
async def list_files():
    files = list_uploaded_files()
    return {"files": [files]}