# Installation

Horizon runs in Docker and works wherever Docker works.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/horizon.git
cd horizon
```

### 2. Docker Compose (Recommended)

```bash
docker-compose up -d
```

The web interface will be available at http://localhost:8001

### 3. Access the Web Interface

Navigate to http://localhost:8001 to access the Horizon web interface.

## Docker Compose Configuration

Example `docker-compose.yml`:

```yaml
version: '3.8'

services:
  horizon:
    build: .
    container_name: horizon
    ports:
      - "8001:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
```

## Data Directory Structure

After first run, you'll have:

```
horizon/
├── data/
│   ├── raw/             # Raw imported data
│   ├── processed/       # Processed profiles
│   └── external/        # Frigate database copies
└── config/              # Configuration files
```

## Accessing the Web Interface

Once running:

- **Web UI**: http://localhost:8001
- **API Docs**: http://localhost:8001/api/docs

## Building from Source

If you need to build the image:

```bash
docker build -t horizon-webui .
```

## Next Steps

After installation:

1. Import your Frigate data - see [Data Import](08-data-import.md)
2. Configure MQTT for real-time processing - see [MQTT](07-mqtt.md)
3. Adjust pattern detection settings - see [Configuration](04-configuration.md)
4. Start analyzing vehicles via the web interface
