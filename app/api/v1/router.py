from fastapi import APIRouter

from app.api.v1.routes import list_files, chat, delete, upload

api_router = APIRouter()

api_router.include_router(list_files.router, tags=["List"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(delete.router, tags=["Delete"])
api_router.include_router(upload.router, tags=["Upload"])