"""
POST/ run-pipeline

Triggers the data engine preporcessing pipline for an upload file.
The job runs in the background thread so the endpoint return immedetiately
"""

import threading 
from pathlib import Path 

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.job_manager import JobStatus 

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent 
RAW_DIR = BASE_DIR / "data" / "raw"

class PipelineRequest(BaseModel):
    file_id: str
    target_column: str | None = None 
    
    
@router.post(
    "/",
    summary="Run the preprocessing pipeline on an uploaded file.",
    response_description="job_id to poll at GET/ report/{job_id}",
    
)
def run_pipeline(body: PipelineRequest, request: Request):
    
    # Locate the uploaded file
    matches = list(RAW_DIR.glob(f"{body.file_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"file_id '{body.file_id}' not found.",      
        )
    raw_path = matches[0]
    jm = request.app.state.job_manager
    job_id = jm.create_job(file_id = body.file_id, filename = raw_path.name)
    
    # Run the pipeline in the background thread 
    thread = threading.Thread(
        target = _run_in_background,
        args=(job_id, raw_path, body.target_column, jm),
        daemon = True,
    )
    thread.start()
    
    return {
        "job_id" : job_id,
        "status": JobStatus.RUNNING,
        "message" : "Pipeline started. Poll GET /report/ {job_id} for results.",
        
    }
    
# Backgrouund worker 

def _run_in_background(job_id: str, raw_path: Path, target: str | None, jm):
    # Execute the pipeline and updates job state on completion / failure.abs
    try:
        from pipeline import run_pipeline as _pipeline 
        from reporting_system.html_reporter import generate_html_report, _health_score 
        
        jm.set_running(job_id)
        
        # Core pipeline 
        report_dict = _pipeline(
            dataset_path=str(raw_path),
            target=target,
            interactive=False,
            )
        
        if report_dict is None:
            jm.set_failed(job_id, "Pipeline rt=eturned no output. Check your data file.")
            return 

        # Health score (same formula used in the HTML report) so the
        # frontend's QUALITY stat box has a real number to display.
        raw_shape = report_dict.get("dataset_shape", [0, 0])
        raw_row_count = raw_shape[0] if isinstance(raw_shape[0], int) else 0
        report_dict["health_score"] = _health_score(
            report_dict.get("quality_report", {}), raw_row_count
        )
        
        # HTML report 
        dataset_name = raw_path.stem 
        html_path = generate_html_report(report_dict, dataset_name)
        
        jm.set_completed(
            job_id,
            report = report_dict,
            html_report_path = str(html_path),
            dataset_name = dataset_name,
        )
        
    except Exception as exc:
        jm.set_failed(job_id, str(exc))