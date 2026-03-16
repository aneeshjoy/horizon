"""
Configuration API endpoints
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from typing import Dict, Optional
from src.webui.services.config_service import get_config_service
from src.webui.models.config import (
    SystemConfig,
    ConfigValidationResult,
    ReprocessStatus,
)


router = APIRouter(prefix="/api/config", tags=["config"])


def _get_profile_manager(request: Request) -> Optional['ProfileManager']:
    """
    Get ProfileManager from MQTT service if available.

    Args:
        request: FastAPI Request object

    Returns:
        ProfileManager instance or None
    """
    from horizon.mqtt.profile_manager import ProfileManager

    mqtt_service = getattr(request.app.state, 'mqtt_service', None)
    if mqtt_service is not None:
        return mqtt_service.profile_manager
    return None


@router.get("", response_model=SystemConfig)
async def get_config():
    """
    Get current system configuration

    Returns all configuration settings with current values.
    These settings control pattern detection, classification,
    display, and prediction behavior.
    """
    service = get_config_service()
    return service.load_config()


@router.put("", response_model=SystemConfig)
async def update_config(
    config: SystemConfig,
    background_tasks: BackgroundTasks,
    reprocess: bool = Query(False, description="Trigger reprocessing with new settings")
):
    """
    Update system configuration

    Updates configuration settings and optionally triggers
    reprocessing of all vehicle profiles with the new settings.

    Note: Reprocessing may take significant time for large datasets.
    Consider the impact before triggering reprocess=true.
    """
    service = get_config_service()

    # Validate before saving
    validation = service.validate_config(config)
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "errors": validation.errors,
                "warnings": validation.warnings
            }
        )

    # Save configuration
    saved_config = service.save_config(config)

    # Note: Reprocessing is now handled by the rebuild service
    # Use the /reprocess/start endpoint to trigger a rebuild

    return saved_config


@router.post("/validate", response_model=ConfigValidationResult)
async def validate_config(config: SystemConfig):
    """
    Validate configuration without applying changes

    Tests configuration values for validity and consistency.
    Returns errors and warnings but does not save changes.

    Use this to test configuration changes before applying them.
    """
    service = get_config_service()
    return service.validate_config(config)


@router.post("/reset", response_model=SystemConfig)
async def reset_config():
    """
    Reset configuration to defaults

    Restores all settings to their default values.
    Does NOT trigger automatic reprocessing.
    """
    service = get_config_service()
    return service.reset_to_defaults()


@router.get("/reprocess/status", response_model=ReprocessStatus)
async def get_reprocess_status(request: Request):
    """
    Get status of ongoing or last reprocessing job

    Returns progress information if a reprocessing job is active,
    or details of the most recently completed job.
    """
    from horizon.rebuild.rebuild_service import get_rebuild_service

    profile_manager = _get_profile_manager(request)
    rebuild_service = get_rebuild_service(profile_manager=profile_manager)

    # Get the most recent job
    job_status = rebuild_service.get_latest_job()
    if job_status:
        # Map rebuild service status to API model
        return ReprocessStatus(
            job_id=job_status['job_id'],
            status=job_status['status'],
            progress=job_status['progress'],
            total_vehicles=0,  # Rebuild service tracks events, not vehicles
            processed_vehicles=job_status.get('processed_events', 0),
            started_at=job_status.get('started_at'),
            completed_at=job_status.get('completed_at'),
            error_message=job_status.get('error_message')
        )

    # Return empty status if no jobs
    return ReprocessStatus(
        job_id="",
        status="none",
        progress=0.0,
        total_vehicles=0,
        processed_vehicles=0,
        started_at=None,
        completed_at=None,
        error_message=None
    )


@router.post("/reprocess/start")
async def start_reprocess(request: Request, background_tasks: BackgroundTasks):
    """
    Start reprocessing all vehicle profiles from JSONL events

    Triggers a background job to rebuild all profiles from frigate_events.jsonl
    using current configuration settings. This may take significant
    time for large datasets.

    Returns the job ID for status tracking.
    """
    from horizon.rebuild.rebuild_service import get_rebuild_service

    profile_manager = _get_profile_manager(request)
    rebuild_service = get_rebuild_service(profile_manager=profile_manager)
    job_id = rebuild_service.start_rebuild()

    return {"job_id": job_id, "message": "Rebuild started"}


@router.post("/reprocess/cancel")
async def cancel_reprocess(request: Request):
    """
    Cancel ongoing reprocessing job

    Attempts to cancel the currently running reprocessing job.
    Already processed events will not be saved.
    """
    from horizon.rebuild.rebuild_service import get_rebuild_service

    profile_manager = _get_profile_manager(request)
    rebuild_service = get_rebuild_service(profile_manager=profile_manager)

    # Get most recent job
    job_status = rebuild_service.get_latest_job()
    if job_status and job_status.get('status') == 'running':
        job_id = job_status['job_id']
        cancelled = rebuild_service.cancel_job(job_id)
        if cancelled:
            return {"message": "Rebuild cancelled", "job_id": job_id}

    return {"message": "No active rebuild job to cancel"}
