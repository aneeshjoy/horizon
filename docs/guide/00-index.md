# Horizon Documentation

Complete user guide for Horizon - License Plate Pattern Analysis System.

## Quick Navigation

### Getting Started

1. [Purpose](01-purpose.md) - What Horizon does and why
2. [Architecture](02-architecture.md) - How it works
3. [Installation](03-installation.md) - Docker setup

### Core Concepts

4. [Pattern Detection](05-pattern-detection.md) - How patterns are detected
5. [Classification](06-classification.md) - How vehicles are classified

### Configuration & Usage

6. [Configuration](04-configuration.md) - All settings explained
7. [MQTT](07-mqtt.md) - Real-time processing
8. [Data Import](08-data-import.md) - Database import
9. [Rebuild](09-rebuild.md) - Reprocessing data
10. [Stats](10-stats.md) - Understanding statistics

## Common Tasks

| Want to... | Go to... |
|------------|----------|
| Set up Horizon | [Installation](03-installation.md) |
| Import Frigate data | [Data Import](08-data-import.md) |
| Configure settings | [Configuration](04-configuration.md) |
| Set up real-time processing | [MQTT](07-mqtt.md) |
| Understand patterns | [Pattern Detection](05-pattern-detection.md) |
| Understand classifications | [Classification](06-classification.md) |
| Change settings and reprocess | [Rebuild](09-rebuild.md) |

## Configuration Quick Reference

| Setting | Default | Purpose |
|---------|---------|---------|
| `bucket_epsilon` | 45 | Pattern time tolerance (minutes) |
| `min_bucket_samples` | 3 | Readings needed for new pattern |
| `min_confidence` | 0.65 | Minimum detection confidence |
| `commuter_threshold` | 60 | RDS for Commuter classification |
| `unknown_threshold` | 40 | RDS for Unknown classification |

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/horizon/issues)
- Frigate: [frigate.io](https://frigate.io/)
