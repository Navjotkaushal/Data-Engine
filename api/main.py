# FastAPI Application entry point 

from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles 
from pathlib import Path 

from api.routes import upload, pipeline, report, health, process 
from core.job_manager import JobManager 

# Output directories 
BASE_DIR = Path(__file__).resolve().parent.parent 
REPORTS_DIR = BASE_DIR / "data" / "output" / "reports" 

# App 

app = FastAPI(
    title= "Data Engine API",
    description=(
        "Upload a CSV or Excel file and receive a cleaned dataset"
                "plus an HTML summary report."
    ),
    version="1.0.0",
    docs_url = "/docs",
    redoc_url= "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Serving generated HTML reports as static files at /reports/<job_id>.html 
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name = "reports")

# Shared state 
app.state.job_manager = JobManager()

# Routes 
app.include_router(health.router, tags = ["Health"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(pipeline.router, prefix="/run-pipeline", tags=["Pipeline"])
app.include_router(report.router, prefix="/report", tags=["Report"])
app.include_router(process.router, prefix="/process", tags=["One-shot"])
