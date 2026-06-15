"""
core/job_manager.py
───────────────────
Thread-safe in-memory job store.
For production use, swap the dict for Redis or a database.
"""
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}

    # ── Write operations ──────────────────────────────────────────────────────

    def create_job(self, file_id: str, filename: str) -> str:
        job_id = str(uuid.uuid4())
        now = _now()
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "file_id": file_id,
                "filename": filename,
                "status": JobStatus.PENDING,
                "created_at": now,
                "updated_at": now,
                "report": None,
                "html_report_path": None,
                "dataset_name": None,
                "error": None,
            }
        return job_id

    def set_running(self, job_id: str):
        self._update(job_id, status=JobStatus.RUNNING)

    def set_completed(
        self,
        job_id: str,
        report: dict,
        html_report_path: str,
        dataset_name: str,
    ):
        self._update(
            job_id,
            status=JobStatus.COMPLETED,
            report=report,
            html_report_path=html_report_path,
            dataset_name=dataset_name,
        )

    def set_failed(self, job_id: str, error: str):
        self._update(job_id, status=JobStatus.FAILED, error=error)

    # ── Read operations ───────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> Optional[dict]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list[dict]:
        with self._lock:
            return list(self._jobs.values())

    # ── Internal ──────────────────────────────────────────────────────────────

    def _update(self, job_id: str, **kwargs):
        with self._lock:
            if job_id not in self._jobs:
                return
            self._jobs[job_id].update(kwargs)
            self._jobs[job_id]["updated_at"] = _now()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()