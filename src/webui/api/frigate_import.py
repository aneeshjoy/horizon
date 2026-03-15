"""
Import API endpoints

Handles importing license plate data from Frigate database.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.webui.models.config import ImportStatus
from src.webui.services.config_service import get_config_service
from horizon.frigate.import_service import get_import_service


router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/start", response_model=dict)
async def start_import(background_tasks: BackgroundTasks):
    """
    Start importing from Frigate database

    Reads the import_config from settings to determine:
    - Database path (import_db_path)
    - Date filter (import_after_date)
    - Auto-rebuild flag (auto_rebuild_after_import)

    The import runs in the background and can be monitored via
    the /status endpoint.

    Returns the job ID for tracking.
    """
    config_service = get_config_service()
    config = config_service.load_config()

    import_config = config.import_config

    if not import_config.auto_import_on_startup:
        raise HTTPException(
            status_code=400,
            detail="Auto import is disabled. Enable it in configuration first."
        )

    import_service = get_import_service()

    try:
        job_id = import_service.start_import(
            db_path=import_config.import_db_path,
            after_date=import_config.import_after_date,
            auto_rebuild=import_config.auto_rebuild_after_import
        )

        return {
            "job_id": job_id,
            "message": "Import started",
            "db_path": import_config.import_db_path,
            "auto_rebuild": import_config.auto_rebuild_after_import
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start import: {str(e)}")


@router.post("/start/manual", response_model=dict)
async def start_manual_import(
    db_path: str,
    after_date: str = None,
    auto_rebuild: bool = True,
    background_tasks: BackgroundTasks = None
):
    """
    Start import with custom parameters

    Allows starting an import without changing configuration.
    Useful for one-time imports or testing.

    Args:
        db_path: Path to Frigate database file
        after_date: Optional date filter (YYYY-MM-DD)
        auto_rebuild: Automatically rebuild profiles after import (default: true)
    """
    import_service = get_import_service()

    try:
        job_id = import_service.start_import(
            db_path=db_path,
            after_date=after_date,
            auto_rebuild=auto_rebuild
        )

        return {
            "job_id": job_id,
            "message": "Import started",
            "db_path": db_path,
            "auto_rebuild": auto_rebuild
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start import: {str(e)}")


@router.get("/status", response_model=ImportStatus)
async def get_import_status():
    """
    Get status of the most recent import job

    Returns detailed progress information including:
    - Current status (pending, running, completed, failed)
    - Progress percentage
    - Events processed/filtered
    - Database size
    """
    import_service = get_import_service()

    job = import_service.get_latest_job()
    if job:
        return ImportStatus(**job)

    # Return empty status if no jobs
    return ImportStatus(
        job_id="",
        status="none",
        progress=0.0,
        total_events=0,
        processed_events=0,
        filtered_events=0,
        plates_created=0,
        started_at=None,
        completed_at=None,
        error_message=None,
        db_path="",
        db_size_mb=0.0,
        rebuild_triggered=False
    )


@router.get("/status/{job_id}", response_model=ImportStatus)
async def get_import_job_status(job_id: str):
    """
    Get status of a specific import job

    Args:
        job_id: The job ID returned from /start
    """
    import_service = get_import_service()

    job = import_service.get_job(job_id)
    if job:
        # Ensure rebuild_triggered is set (default to False if missing)
        if 'rebuild_triggered' not in job:
            job['rebuild_triggered'] = False
        return ImportStatus(**job)

    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.post("/cancel")
async def cancel_import():
    """
    Cancel the currently running import job

    Events already processed will remain in the events file.
    The rebuild process can be run separately.
    """
    import_service = get_import_service()

    job = import_service.get_latest_job()
    if job and job.get('status') == 'running':
        job_id = job['job_id']
        cancelled = import_service.cancel_import(job_id)
        if cancelled:
            return {"message": "Import cancelled", "job_id": job_id}

    return {"message": "No active import job to cancel"}


@router.get("/check")
async def check_database(db_path: str):
    """
    Check if a database file exists and contains license plate data

    Args:
        db_path: Path to Frigate database file

    Returns information about the database including:
    - File existence
    - File size
    - Estimated event count
    - Schema type detected
    """
    import os
    import sqlite3

    if not os.path.exists(db_path):
        return {
            "exists": False,
            "error": "File not found"
        }

    try:
        size_mb = os.path.getsize(db_path) / (1024 * 1024)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Detect schema and count events
        info = {
            "exists": True,
            "size_mb": round(size_mb, 2),
            "tables": [],
            "event_count": 0,
            "schema_type": "unknown"
        }

        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        info["tables"] = tables

        # Detect schema and count
        if "plate_detections" in tables:
            cursor.execute("SELECT COUNT(*) FROM plate_detections WHERE confidence > 0.65")
            info["event_count"] = cursor.fetchone()[0]
            info["schema_type"] = "plate_detections"

        if info["event_count"] == 0 and "event_detections" in tables:
            cursor.execute("""
                SELECT COUNT(*) FROM event_detections
                WHERE label = 'license_plate'
            """)
            info["event_count"] = cursor.fetchone()[0]
            if info["event_count"] > 0:
                info["schema_type"] = "event_detections"

        if info["event_count"] == 0 and "events" in tables:
            cursor.execute("""
                SELECT COUNT(*) FROM events
                WHERE label = 'license_plate'
            """)
            info["event_count"] = cursor.fetchone()[0]
            if info["event_count"] > 0:
                info["schema_type"] = "events"

        conn.close()

        return info

    except Exception as e:
        return {
            "exists": True,
            "error": str(e)
        }
