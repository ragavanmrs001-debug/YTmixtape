"""
Shared utility helpers for the YT Mixtape application.

Provides file-listing, directory creation, unique naming,
and lightweight job-status tracking.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.config import AUDIO_FORMATS

logger = logging.getLogger(__name__)

# ── In-memory job store (swap for Redis / DB in production) ─────────
_jobs: Dict[str, Dict[str, Any]] = {}


# ── File Helpers ─────────────────────────────────────────────────────

def list_audio_files(folder: str) -> list:
    """Return sorted list of audio filenames in *folder*."""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")
    files = sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(AUDIO_FORMATS)
        and not f.startswith(".")
    )
    if not files:
        raise ValueError(f"No audio files found in: {folder}")
    return files


def list_image_files(folder: str) -> list:
    """Return sorted list of image filenames in *folder*."""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")
    image_exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    files = sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(image_exts)
        and not f.startswith(".")
    )
    return files


def ensure_dir(path: str) -> str:
    """Create *path* (and parents) if it doesn't exist. Returns *path*."""
    os.makedirs(path, exist_ok=True)
    return path


def get_unique_filename(prefix: str, ext: str) -> str:
    """Generate a collision-free filename like ``prefix_20260807_143012_a1b2c3.ext``."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{short_id}{ext}"


# ── Job Status Helpers ───────────────────────────────────────────────

def create_job(job_id: str, description: str = "") -> Dict[str, Any]:
    """Register a new job."""
    job = {
        "job_id": job_id,
        "status": "pending",
        "description": description,
        "created_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
    }
    _jobs[job_id] = job
    logger.info("Job created: %s – %s", job_id, description)
    return job


def update_job(job_id: str, *, status: str = None,
               result: Any = None, error: str = None) -> None:
    """Update fields on an existing job."""
    if job_id not in _jobs:
        return
    if status:
        _jobs[job_id]["status"] = status
    if result is not None:
        _jobs[job_id]["result"] = result
    if error is not None:
        _jobs[job_id]["error"] = error


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a job by id, or ``None``."""
    return _jobs.get(job_id)
