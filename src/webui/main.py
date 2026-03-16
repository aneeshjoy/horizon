"""
Horizon Web UI - FastAPI Application

Main entry point for the Horizon License Plate Pattern Analysis System web interface.
"""

import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.webui.api import vehicles, search, config, status, frigate_import

# Configure root logger to DEBUG level
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, logging.INFO)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(numeric_level)

# Add console handler if not already present
if not root_logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

# Also configure specific loggers
logging.getLogger("horizon").setLevel(numeric_level)
logging.getLogger("webui").setLevel(numeric_level)
logging.getLogger("uvicorn").setLevel(numeric_level)
logging.getLogger("uvicorn.error").setLevel(numeric_level)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)  # Keep access logs at INFO

print(f"Root logger level set to {log_level}")

# Create FastAPI app
app = FastAPI(
    title="Horizon License Plate Analysis",
    description="Web UI for the Horizon License Plate Pattern Analysis System",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(vehicles.router)
app.include_router(search.router)
app.include_router(config.router)
app.include_router(status.router)
app.include_router(frigate_import.router)


# API info endpoint
@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Horizon Web UI API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "status": "operational"
    }


# Serve static files (React build output)
static_dir = Path(__file__).parent / "static" / "dist"
if static_dir.exists():
    # Mount static files for assets
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    # Serve the SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA"""
        # Check if it's an API route - let those pass through
        if full_path.startswith("api/"):
            return {"error": "API route not found"}

        # Try to serve the file directly
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        # Return index.html for SPA routing
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

        return {"error": "Frontend not built. Run 'npm run build' in frontend/"}
else:
    @app.get("/{full_path:path}")
    async def frontend_not_built(full_path: str):
        """Message when frontend is not built"""
        return {
            "message": "Frontend not built",
            "instructions": "Run 'npm run build' in frontend/ directory",
            "api_docs": "/api/docs"
        }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Ensure config directory exists
    from src.webui.services.config_service import get_config_service

    config_service = get_config_service()
    print(f"Configuration loaded from: {config_service.config_file}")

    # Load system config
    system_config = config_service.load_config()

    # Auto-import from Frigate DB if enabled
    import_config = system_config.import_config
    if import_config.auto_import_on_startup:
        print(f"Auto-import enabled: {import_config.import_db_path}")
        from horizon.frigate.import_service import get_import_service

        import_service = get_import_service()
        try:
            job_id = import_service.start_import(
                db_path=import_config.import_db_path,
                after_date=import_config.import_after_date
            )
            print(f"Import job started: {job_id}")
        except FileNotFoundError as e:
            print(f"Auto-import skipped: {e}")
        except Exception as e:
            print(f"Auto-import failed: {e}")
    else:
        print("Auto-import disabled in configuration")

    # Initialize MQTT service if enabled
    mqtt_config = system_config.mqtt

    if mqtt_config.enabled:
        print(f"Starting MQTT service ({mqtt_config.broker_host}:{mqtt_config.broker_port})...")

        from horizon.mqtt.service import MQTTService

        app.state.mqtt_service = MQTTService(
            mqtt_config=mqtt_config,
            pattern_config=system_config.pattern_detection
        )

        # Start MQTT service in background
        started = await app.state.mqtt_service.start()

        if started:
            print("MQTT service started successfully")

            # Inject ProfileManager into import service for coordinated rebuilds
            from horizon.frigate.import_service import get_import_service
            import_service = get_import_service(profile_manager=app.state.mqtt_service.profile_manager)
            print("ProfileManager coordination enabled for rebuild service")
        else:
            print("Failed to start MQTT service")
            app.state.mqtt_service = None
    else:
        print("MQTT service disabled in configuration")
        app.state.mqtt_service = None


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down Horizon Web UI")

    # Stop MQTT service if running
    if hasattr(app.state, 'mqtt_service') and app.state.mqtt_service is not None:
        print("Stopping MQTT service...")
        await app.state.mqtt_service.stop()
        print("MQTT service stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.webui.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
