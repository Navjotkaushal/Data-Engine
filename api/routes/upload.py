# Post/ upload 

"""
Accepts a CSV file, validate its size and type 
"""

from __future__ import annotations 

from fastapi import APIRouter, Depends, UploadFile, File
from config.settings import Settings 
from api.dependencies import get_settings 
from core.exceptions import FileTooLargeError, UnsupportedFileTypeError 
from core.schemas import UploadResponse 


router = APIRouter(tags=["Upload"])

ALLOWED_CONTENT_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel"}
ALLOWED_EXTENSIONS = {".csv"}


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    cfg: Settings = Depends(get_settings),
)-> UploadResponse:
    
    """
    Upload a CSV dataset.
 
    - Max size is controlled by `MAX_UPLOAD_SIZE_MB` in .env (default 50 MB).
    - Only .csv files are accepted.
    - Returns the saved filename. Pass this to POST /run-pipeline.
    
    """
    # Type Check:
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(received = suffix or file.content_type)
    
    
    # Size check: read in chunks to avoid loading the whole file in memory
    dest = cfg.upload_dir / file.filename
    size = 0 
    max_bytes = cfg.max_upload_bytes 
    
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 256): # 256 KB Chunks
            size += len(chunk)
            if size > max_bytes:
                dest.unlink(missing_ok = True)
                raise FileTooLargeError(max_mb = cfg.max_upload_size_mb)
            out.write(chunk)
            
    return UploadResponse(filename = file.filename)

