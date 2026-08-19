from fastapi import APIRouter
from src.pipeline import ask
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
async def chat(request: ChatRequest):
    response = ask(request.query)
    return response