"""
GET /report/{job_id}         – JSON status + summary
GET /report/{job_id}/csv     – Download cleaned CSV
GET /report/{job_id}/html    – Redirect to the HTML summary page
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse

from core.job_manager import JobStatus

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEANED_DIR = BASE_DIR / "data" / "output" / "cleaned_data"


# ── GET /report/{job_id} ──────────────────────────────────────────────────────

@router.get(
    "/{job_id}",
    summary="Get job status and preprocessing summary",
)
def get_report(job_id: str, request: Request):
    """
    Returns the current state of a pipeline job.

    - `status`: `running` | `completed` | `failed`
    - `summary`: full preprocessing report (when completed)
    - `downloads.csv`: URL to download the cleaned CSV
    - `downloads.html_report`: URL to view the HTML summary page
    """
    jm = request.app.state.job_manager
    job = jm.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    base_url = str(request.base_url).rstrip("/")

    response: dict = {
        "job_id": job_id,
        "status": job["status"],
        "file_id": job.get("file_id"),
        "filename": job.get("filename"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
    }

    if job["status"] == JobStatus.COMPLETED:
        dataset_name = job.get("dataset_name", job.get("file_id", job_id))
        response["summary"] = job.get("report", {})
        response["downloads"] = {
            "csv": f"{base_url}/report/{job_id}/csv",
            "html_report": f"{base_url}/reports/{dataset_name}_report.html",
        }

    elif job["status"] == JobStatus.FAILED:
        response["error"] = job.get("error")

    return response


# ── GET /report/{job_id}/csv ──────────────────────────────────────────────────

@router.get(
    "/{job_id}/csv",
    summary="Download the cleaned CSV file",
)
def download_csv(job_id: str, request: Request):
    jm = request.app.state.job_manager
    job = jm.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not completed yet (status: {job['status']}).",
        )

    dataset_name = job.get("dataset_name", job_id)
    csv_path = CLEANED_DIR / f"{dataset_name}_cleaned.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Cleaned CSV not found on disk.")

    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=f"{dataset_name}_cleaned.csv",
    )


# ── GET /report/{job_id}/html ─────────────────────────────────────────────────

@router.get(
    "/{job_id}/html",
    summary="View the HTML summary report",
)
def view_html_report(job_id: str, request: Request):
    jm = request.app.state.job_manager
    job = jm.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not completed yet (status: {job['status']}).",
        )

    dataset_name = job.get("dataset_name", job_id)
    base_url = str(request.base_url).rstrip("/")
    return RedirectResponse(url=f"{base_url}/reports/{dataset_name}_report.html")