from fastapi import APIRouter 
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health", summary="Service health check")
def health_check():
    return{
        "status": "ok",
        "service": "Data Engine API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }