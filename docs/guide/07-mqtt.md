# MQTT Integration

MQTT integration allows Horizon to process license plate detections in real-time as Frigate publishes them.

## Import vs MQTT

| Feature | Import | MQTT |
|---------|--------|------|
| Data source | Frigate database | Live MQTT stream |
| Processing | Batch, on-demand | Real-time |
| Latency | Minutes/hours | Milliseconds |
| Use case | Historical data | Live monitoring |
| Setup complexity | Simple | Requires MQTT config |

**Use MQTT when**:
- You need real-time alerts
- Want immediate pattern updates
- Monitoring active areas

**Use Import when**:
- Analyzing historical data
- Initial setup
- MQTT not available

## Setup

### 1. Configure Frigate MQTT

Ensure Frigate is publishing license plate events. In your Frigate config:

```yaml
mqtt:
  host: mqtt-broker
  port: 1883
  topic_prefix: frigate
```

Frigate publishes to topics like:
- `frigate/{camera}/license_plate`
- `frigate/events`

### 2. Configure Horizon MQTT

Via web interface at http://localhost:8000/config:

```yaml
mqtt_broker: frigate          # MQTT broker hostname
mqtt_port: 1883               # MQTT port
mqtt_topic: frigate/+/license_plate
mqtt_username: null           # Optional auth
mqtt_password: null           # Optional auth
mqtt_auto_start: true         # Start on startup
```

Or via environment variables:

```yaml
environment:
  - MQTT_BROKER=frigate
  - MQTT_PORT=1883
  - MQTT_TOPIC=frigate/+/license_plate
```

### 3. Start the Listener

The listener starts automatically if `mqtt_auto_start: true`.

Manual control via web interface:
- **Start**: Begin processing MQTT messages
- **Stop**: Pause processing
- **Status**: View connection state and statistics

## Topic Subscription

### Wildcard Topics

Horizon uses MQTT wildcards to subscribe to all cameras:

```
frigate/+/license_plate
```

This subscribes to:
- `frigate/driveway/license_plate`
- `frigate/parking/license_plate`
- `frigate/gate/license_plate`

### Custom Topics

Subscribe to specific cameras:

```yaml
mqtt_topic: frigate/driveway/license_plate
```

Or all events:

```yaml
mqtt_topic: frigate/events
```

## Message Format

Frigate publishes license plate detections as:

```json
{
  "type": "license_plate",
  "event_id": "123456789",
  "camera": "driveway",
  "label": "license_plate",
  "timestamp": "2026-03-15T08:30:00Z",
  "data": {
    "plate": "ABC-123",
    "confidence": 0.92,
    "box": [100, 200, 300, 400]
  }
}
```

Horizon extracts:
- Plate text
- Timestamp
- Confidence score

## Processing Flow

```
Frigate detects plate
        ↓
  Publishes to MQTT
        ↓
  Horizon receives
        ↓
  Deduplication check
  (within 5 sec window)
        ↓
  Process reading
  - OCR correction
  - Confidence filter
  - Pattern matching
        ↓
  Update profiles
        ↓
  Save to JSON
```

## Deduplication

Frigate may publish the same plate multiple times (different frames).

**Dedup window**: 5 seconds (default)

Within the window, identical plates from the same camera are ignored.

**Configure**:

```yaml
mqtt_dedup_window: 5000  # milliseconds
```

**Disable**:

```yaml
mqtt_dedup_window: 0  # Process every message
```

## Authentication

If your MQTT broker requires authentication:

```yaml
mqtt_broker: mqtt.example.com
mqtt_port: 8883
mqtt_username: horizon_user
mqtt_password: secure_password
mqtt_use_tls: true
```

## Statistics

View MQTT processing stats in the web interface:

| Metric | Description |
|--------|-------------|
| Messages received | Total MQTT messages processed |
| Readings processed | Plates after deduplication |
| Readings filtered | Plates below confidence threshold |
| Patterns updated | Buckets that were modified |
| New patterns | New buckets created |
| Processing rate | Messages/second |

## Troubleshooting

### No Messages Received

**Check**:
1. Frigate is publishing license plates
2. MQTT broker hostname is correct
3. Network connectivity between containers
4. Topic matches Frigate's publish pattern

**Debug**:
```bash
# Subscribe to topic manually
docker-compose exec horizon mosquitto_sub -h frigate -t 'frigate/+/license_plate' -v
```

### Connection Refused

**Check**:
1. MQTT broker is running
2. Port is correct (default 1883)
3. No firewall blocking connection
4. Credentials are correct (if auth enabled)

### All Messages Filtered

**Check**:
1. `min_confidence` not too high
2. License plates are being detected in Frigate UI
3. Confidence scores in MQTT messages

### High Latency

**Check**:
1. System resources (CPU, memory)
2. Disk I/O (profile writes)
3. Network latency to MQTT broker

## Performance

MQTT processing is lightweight:

| Metric | Value |
|--------|-------|
| Latency | ~10ms per message |
| Throughput | 100+ messages/second |
| Memory | ~50MB for listener |
| CPU | Low (<5% per core) |

## Best Practices

1. **Start with import**: Use database import first to establish baseline patterns
2. **Enable auto-start**: Automatically process on startup
3. **Monitor dedup**: Adjust window based on your camera's frame rate
4. **Use wildcards**: Subscribe to all cameras, not specific ones
5. **Check stats**: Review processing statistics regularly

## Advanced: Custom Message Processing

For custom MQTT message formats, extend the MQTT processor:

```python
from horizon.mqtt.processor import MQTTProcessor

class CustomProcessor(MQTTProcessor):
    def extract_plate_data(self, message):
        # Custom parsing logic
        return {
            'plate': message['custom_plate_field'],
            'timestamp': message['time'],
            'confidence': message['score']
        }
```

## Related Topics

- [Pattern Detection](05-pattern-detection.md) - How patterns are detected
- [Classification](06-classification.md) - How vehicles are classified
- [Data Import](08-data-import.md) - Alternative to MQTT
- [Configuration](04-configuration.md) - All configuration options
