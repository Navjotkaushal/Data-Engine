"""
POST /process  (convenience one-shot endpoint)
───────────────────────────────────────────────
Upload a file, run the full pipeline, and receive BOTH outputs in a
single multipart response — no polling required.

Great for small files or scripted workflows where async is not needed.
"""
import io
import json
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEANED_DIR = BASE_DIR / "data" / "output" / "cleaned_data"
REPORTS_DIR = BASE_DIR / "data" / "output" / "reports"


@router.post(
    "/",
    summary="Upload, preprocess and download results in one request",
    response_description="A ZIP file containing cleaned.csv and report.html",
)
async def process(
    file: UploadFile = File(..., description="Raw CSV or Excel file to preprocess"),
    target_column: str | None = Form(None, description="Optional target/label column name"),
):
    """
    **One-shot endpoint** – upload your file and receive a ZIP containing:

    - `<name>_cleaned.csv` — the cleaned dataset
    - `<name>_report.html` — the HTML summary page
    - `report.json` — the full JSON report

    Blocks until the pipeline completes (suitable for files ≤ ~10 MB).
    For larger files use `POST /upload` + `POST /run-pipeline` + `GET /report/{job_id}`.
    """
    import uuid
    from pipeline import run_pipeline
    from reporting_system.html_reporter import generate_html_report

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{suffix}'.")

    # Write upload to a temp file so pipeline can read it by path
    dataset_name = f"process_{uuid.uuid4().hex[:8]}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        report_dict = run_pipeline(
            dataset_path=str(tmp_path),
            target=target_column,
            interactive=False,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    if report_dict is None:
        raise HTTPException(status_code=422, detail="Pipeline failed. Check the uploaded file.")

    html_path = generate_html_report(report_dict, dataset_name)
    csv_path  = CLEANED_DIR / f"{dataset_name}_cleaned.csv"

    # Build in-memory ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if csv_path.exists():
            zf.write(csv_path,  arcname=f"{dataset_name}_cleaned.csv")
        if html_path.exists():
            zf.write(html_path, arcname=f"{dataset_name}_report.html")
        zf.writestr("report.json", json.dumps(report_dict, indent=2, default=str))
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{dataset_name}_results.zip"'},
    )