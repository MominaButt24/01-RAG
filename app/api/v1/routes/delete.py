from fastapi import APIRouter
from src.pipeline import delete_uploaded_files
from pydantic import BaseModel

router = APIRouter()

class DeleteRequest(BaseModel):
    filenames: list[str]

@router.delete("/delete")
async def delete(request: DeleteRequest):
    deleted = delete_uploaded_files(request.filenames)
    # return {"deleted": deleted}
    not_found = list(set(request.filenames) - set(deleted))
    return {"deleted": deleted, "not_found": not_found}