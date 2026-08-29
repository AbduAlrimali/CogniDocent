from fastapi import APIRouter

router = APIRouter(prefix="/dev", tags=["Development"])

@router.get("/status")
async def dev_status():
    """
    Dummy endpoint for development status check.
    """
    return {"status": "development mode active"}
