# Data Import

Importing historical Frigate data into Horizon for pattern analysis.

## Import vs MQTT

| Feature | Import | MQTT |
|---------|--------|------|
| Data source | Frigate database | Live MQTT stream |
| Processing | Batch, on-demand | Real-time |
| Latency | Minutes/hours | Milliseconds |
| Setup | Simple | Requires MQTT config |
| Best for | Historical analysis, initial setup | Live monitoring |

**Use Import when**:
- Setting up Horizon for the first time
- Analyzing historical data
- MQTT not available or configured

## Quick Start

### 1. Copy Frigate Database

```bash
# From Docker container
docker cp frigate:/config/frigate.db ./data/external/frigate.db

# Via SCP
scp user@frigate-host:/config/frigate/storage/frigate.db ./data/external/frigate.db

# From shared volume
cp /path/to/frigate/share/frigate.db ./data/external/frigate.db
```

### 2. Import via Web Interface

Navigate to http://localhost:8001/config and:

1. Enable "Auto-import on startup" under Import Settings
2. Set the database path to `/app/data/external/frigate.db` (or your custom path)
3. Click "Import from Database" to start the import

### 3. Verify Results

Check the web interface at http://localhost:8001 for imported vehicles.

## Import Settings

### Database Path

Set the path to your Frigate database in the web interface:
- Navigate to http://localhost:8001/config
- Under "Import Settings", set "Database Path"
- Default: `/app/data/external/frigate.db`

### Confidence Threshold

Readings below threshold are skipped:

**Default**: 0.65 (65%)

Adjust based on your camera quality:
- **High quality**: 0.75-0.80 (stricter)
- **Low quality**: 0.50-0.60 (more lenient)

Configure in the web interface under "Pattern Detection Settings" → "Minimum Confidence"

### Auto-Import on Startup

Enable to automatically import when Horizon starts:
1. Navigate to http://localhost:8001/config
2. Under "Import Settings", enable "Auto-import on startup"
3. This will import from the database each time the container starts

### Auto-Rebuild After Import

Automatically rebuild patterns after importing:
1. Enable "Auto-rebuild after import" in Import Settings
2. Useful for ensuring patterns are up-to-date after new data

## Database Schema Support

Horizon supports multiple Frigate database schemas and auto-detects them on import.

## Troubleshooting

### "No license plate data found"

**Causes**:
1. Frigate hasn't detected any plates yet
2. LPR not enabled in Frigate config
3. Wrong database file

**Solutions**:
1. Check Frigate UI for license plate detections
2. Enable LPR in Frigate config
3. Verify database path is correct

### "Database is locked"

**Cause**: Frigate is currently using the database

**Solutions**:
```bash
# Stop Frigate temporarily
docker-compose stop frigate
docker cp frigate:/config/frigate.db ./data/external/frigate.db
docker-compose start frigate

# Or use sqlite backup
docker exec frigate sqlite3 /config/frigate.db ".backup /tmp/backup.db"
docker cp frigate:/tmp/backup.db ./data/external/frigate.db
```

### "Could not parse timestamp"

**Cause**: Timestamp format varies by Frigate version

**Solution**: Horizon auto-detects common formats. If issues persist, report the specific format.

### Too Many/Few Readings Imported

**Adjust confidence threshold**:
```yaml
min_confidence: 0.50  # More readings
min_confidence: 0.80  # Fewer readings
```

Configure this in the web interface under "Pattern Detection Settings" → "Minimum Confidence".

## Best Practices

1. **Initial import**: Use replace mode for first import
2. **Regular updates**: Use update mode for incremental additions
3. **Backup first**: Copy database before importing
4. **Stop Frigate**: Prevent database locks during copy
5. **Verify after**: Check vehicle counts match expectations
6. **Schedule updates**: Set up automated regular imports

## Related Topics

- [MQTT](07-mqtt.md) - Real-time alternative to import
- [Pattern Detection](05-pattern-detection.md) - What happens after import
- [Configuration](04-configuration.md) - Adjusting import settings
- [Rebuild](09-rebuild.md) - Reprocessing with new settings
