"""
Post / upload 

Accepts a csv os Excel file and save it to data/raw/.
Returns a file_id that you pass to POST/ run-pipeline
"""
import shutil 
import uuid 
from pathlib import Path 

from fastapi import APIRouter, File, HTTPException, Request, UploadFile 

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent 
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv",".xlsx",".xls"}
MAX_SIZE_MB = 50 

@router.post(
    "/",
    summary="Upload a raw data file",
    response_description="file_id to use with /run-pipeline",
)
async def upload_file(request: Request, file: UploadFile= File(...)):
    
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix}' . Accepted: {ALLOWED_EXTENSIONS}",
            
        )
        
    file_id = str(uuid.uuid4())
    dest = RAW_DIR / f"{file_id}{suffix}"
    
    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_SIZE_MB * 1024 * 1024:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"file exceeds {MAX_SIZE_MB} MB limit.",
                )
            out.write(chunk)
        
    return {
        "file_id": file_id,
        "original_filename": file.filename,
        "size_bytes": size,
        "message": "File uploaded successfully. Use file_id with POST/ run-pipeline"
    }
    