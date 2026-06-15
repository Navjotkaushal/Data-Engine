"""
tests/test_api.py
─────────────────
FastAPI route tests using TestClient.
Run with:  pytest tests/test_api.py -v
"""
import io
import json
import time

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ── /health ───────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── /upload ───────────────────────────────────────────────────────────────────

def _csv_bytes(content="col_a,col_b\n1,2\n3,4\n"):
    return io.BytesIO(content.encode())


def test_upload_valid_csv():
    r = client.post(
        "/upload/",
        files={"file": ("test.csv", _csv_bytes(), "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert "file_id" in body
    return body["file_id"]


def test_upload_invalid_extension():
    r = client.post(
        "/upload/",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 415


# ── /run-pipeline ─────────────────────────────────────────────────────────────

def test_run_pipeline_unknown_file():
    r = client.post("/run-pipeline/", json={"file_id": "does-not-exist"})
    assert r.status_code == 404


def test_full_async_flow(tmp_path):
    """Upload → run-pipeline → poll /report/{job_id}"""
    # 1. Upload
    up = client.post(
        "/upload/",
        files={"file": ("sample.csv", _csv_bytes(), "text/csv")},
    )
    assert up.status_code == 200
    file_id = up.json()["file_id"]

    # 2. Run pipeline
    rp = client.post("/run-pipeline/", json={"file_id": file_id})
    assert rp.status_code == 200
    job_id = rp.json()["job_id"]

    # 3. Poll until done (max 30 s)
    for _ in range(30):
        rep = client.get(f"/report/{job_id}")
        assert rep.status_code == 200
        status = rep.json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(1)

    assert status == "completed", f"Pipeline failed: {rep.json().get('error')}"
    assert "summary" in rep.json()
    assert "downloads" in rep.json()


# ── /report ───────────────────────────────────────────────────────────────────

def test_report_not_found():
    r = client.get("/report/nonexistent-job-id")
    assert r.status_code == 404


def test_csv_download_before_completion():
    """Trying to download CSV before pipeline runs should 404 or 409."""
    up = client.post(
        "/upload/",
        files={"file": ("x.csv", _csv_bytes(), "text/csv")},
    )
    file_id = up.json()["file_id"]
    rp = client.post("/run-pipeline/", json={"file_id": file_id})
    job_id = rp.json()["job_id"]

    # Immediately try to download – job is likely still running
    r = client.get(f"/report/{job_id}/csv")
    assert r.status_code in (200, 409)  # 200 if machine is very fast