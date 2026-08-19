import os
import shutil

from fastapi import APIRouter, UploadFile, File

from src.pipeline import ingest_file
from src.config import UPLOAD_DIR

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks_stored = ingest_file(dest_path)
    return {"filename": file.filename, "chunks_stored": chunks_stored}
