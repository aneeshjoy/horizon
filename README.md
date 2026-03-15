# Horizon

License Plate Pattern Analysis System for [Frigate](https://github.com/blakeblackshear/frigate).

Horizon analyzes license plate readings to detect vehicle visitation patterns and classify behavior (Commuter, Unknown, Suspicious).

## Features

- Real-time pattern detection (~110 readings/second)
- Vehicle classification based on routine deviation
- OCR error correction for noisy reads
- Web interface for pattern visualization
- MQTT integration for live processing
- Frigate database import

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/yourusername/horizon.git
cd horizon
docker-compose up -d
```

Web interface: http://localhost:8001

### Import Frigate Data

**Option 1: Copy database (one-time import)**

```bash
# Copy your Frigate database to Horizon's data folder
docker cp frigate:/config/frigate.db ./data/external/frigate.db

# Restart Horizon to trigger auto-import
docker-compose restart horizon
```

Or use the web interface:
1. Navigate to http://localhost:8001/config
2. Enable "Auto-import on startup"
3. Click "Import from Database"

**Option 2: Docker volume mount (continuous access)**

Uncomment and modify the volume mount in `docker-compose.yml`:
```yaml
volumes:
  - frigate-db:/app/data/external:ro
```

See the import instructions in `docker-compose.yml` for complete setup options.

### Set up MQTT (Real-time)

Navigate to http://localhost:8001/config and configure:
- MQTT broker: `frigate` (or your broker address)
- Port: `1883`
- Topic: `frigate/+/license_plate`

## Documentation

Full documentation: [docs/guide/00-index.md](docs/guide/00-index.md)

- [Purpose](docs/guide/01-purpose.md) - What Horizon does
- [Architecture](docs/guide/02-architecture.md) - How it works
- [Installation](docs/guide/03-installation.md) - Setup guide
- [Configuration](docs/guide/04-configuration.md) - All settings
- [Pattern Detection](docs/guide/05-pattern-detection.md) - How patterns work
- [Classification](docs/guide/06-classification.md) - Vehicle classification
- [MQTT](docs/guide/07-mqtt.md) - Real-time processing
- [Data Import](docs/guide/08-data-import.md) - Database import
- [Rebuild](docs/guide/09-rebuild.md) - Reprocessing data
- [Stats](docs/guide/10-stats.md) - Statistics

## Project Structure

```
horizon/
├── src/horizon/          # Core Python code
│   ├── processor.py      # Pattern detection
│   ├── analysis.py       # Vehicle classification
│   ├── mqtt/             # MQTT integration
│   └── frigate/          # Frigate integration
├── src/webui/            # Web interface (FastAPI)
├── frontend/             # React UI
├── docs/guide/           # Documentation
└── docker-compose.yml    # Docker setup
```

## Configuration

All settings are available via the web interface at http://localhost:8001/config

## License

MIT
