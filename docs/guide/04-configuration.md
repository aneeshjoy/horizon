# Configuration

Horizon is configured through the web interface or environment variables. All settings are persisted and can be modified without restarting.

## Configuration Methods

### Web Interface (Recommended)

Navigate to http://localhost:8000 and click **Configuration**. All settings are applied immediately.

### Environment Variables

Set before starting the container:

```bash
environment:
  - HORIZON_BUCKET_EPS=45
  - HORIZON_MIN_CONFIDENCE=0.65
```

## Pattern Detection Settings

### Bucket Epsilon

**What it does**: Tolerance for matching readings to existing patterns (in minutes)

**Default**: `45`

**How it works**:
- A reading at 8:30 AM matches a bucket at 8:00 AM (30 min difference)
- A reading at 9:00 AM does NOT match (60 min difference)

**When to adjust**:
- **Increase** (60-90): Creates fewer, broader patterns
- **Decrease** (15-30): Creates more precise, narrow patterns

**Example**:
```yaml
bucket_epsilon: 45  # Default - good for most cases
bucket_epsilon: 60  # More lenient grouping
bucket_epsilon: 30  # Stricter time matching
```

### Minimum Bucket Samples

**What it does**: Minimum readings required to create a new pattern

**Default**: `3`

**How it works**:
- Readings go to "pending" until enough accumulate at similar times
- 3+ readings within tolerance → new pattern created

**When to adjust**:
- **Increase** (4-5): Reduces false patterns, requires more data
- **Decrease** (2): More sensitive, detects patterns faster

**Example**:
```yaml
min_bucket_samples: 3  # Default - balanced
min_bucket_samples: 5  # More conservative
min_bucket_samples: 2  # More aggressive
```

## Classification Settings

### RDS Thresholds

Routine Deviation Score (RDS) determines vehicle classification.

**Default thresholds**:

| Classification | RDS Range |
|---------------|-----------|
| Commuter | 60-100% |
| Unknown | 40-59% |
| Suspicious | 0-39% |

**Adjusting thresholds**:

```yaml
# More strict - higher bar for "Commuter"
commuter_threshold: 70
unknown_threshold: 50

# More lenient - easier to be "Commuter"
commuter_threshold: 50
unknown_threshold: 30
```

### Pattern Adherence Weight

**What it does**: How much pattern matching affects classification (0-100%)

**Default**: `40%`

**Increase**: Makes pattern consistency more important
**Decrease**: Reduces pattern matching importance

### Confidence Stability Weight

**What it does**: How much detection confidence affects classification (0-100%)

**Default**: `30%`

**Increase**: Prioritizes high-confidence detections
**Decrease**: More tolerant of variable confidence

### Pattern Concentration Weight

**What it does**: How much pattern distribution affects classification (0-100%)

**Default**: `30%`

**Increase**: Favors vehicles with concentrated patterns
**Decrease**: More tolerant of scattered patterns

**Note**: Weights must sum to 100%

## Confidence Filtering

### Minimum Confidence

**What it does**: Filters out low-confidence license plate reads

**Default**: `0.65` (65%)

**When to adjust**:
- **Increase** (0.75-0.80): For high-quality cameras, reduces false positives
- **Decrease** (0.50-0.60): For challenging conditions, captures more reads

**Example**:
```yaml
min_confidence: 0.65  # Default
min_confidence: 0.75  # Stricter - better cameras
min_confidence: 0.50  # More lenient - poor conditions
```

## MQTT Settings

### Connection

```yaml
mqtt_broker: frigate        # Frigate host
mqtt_port: 1883             # Default MQTT port
mqtt_topic: frigate/+/license_plate
mqtt_username: null         # Optional auth
mqtt_password: null         # Optional auth
```

### Processing

```yaml
mqtt_dedup_window: 5000    # Deduplication window (ms)
mqtt_auto_start: true      # Start listener on startup
```

See [MQTT](07-mqtt.md) for complete MQTT configuration.

## OCR Correction Settings

### Similarity Threshold

**What it does**: Threshold for fuzzy matching noisy plate reads to known vehicles

**Default**: `0.85` (85%)

**When to adjust**:
- **Increase** (0.90-0.95): More strict matching, fewer corrections
- **Decrease** (0.75-0.80): More aggressive correction

**Example**:
```yaml
ocr_similarity_threshold: 0.85  # Default
ocr_similarity_threshold: 0.90  # Stricter
ocr_similarity_threshold: 0.80  # More aggressive
```

## Display Settings

### Time Format

```yaml
time_format: 24h    # 24-hour format (08:30)
time_format: 12h    # 12-hour format (8:30 AM)
```

### Date Format

```yaml
date_format: iso      # 2026-03-15
date_format: us       # 03/15/2026
date_format: eu       # 15/03/2026
```

## Complete Configuration Example

```yaml
# Pattern Detection
bucket_epsilon: 45
min_bucket_samples: 3

# Classification
commuter_threshold: 60
unknown_threshold: 40
pattern_adherence_weight: 40
confidence_stability_weight: 30
pattern_concentration_weight: 30

# Filtering
min_confidence: 0.65
ocr_similarity_threshold: 0.85

# MQTT
mqtt_broker: frigate
mqtt_port: 1883
mqtt_topic: frigate/+/license_plate
mqtt_dedup_window: 5000
mqtt_auto_start: true

# Display
time_format: 24h
date_format: iso
```

## Applying Configuration Changes

### Web Interface

Changes apply immediately. No restart needed.

### Environment Variables

Restart the container:

```bash
docker-compose restart
```

### When to Rebuild

After changing pattern detection settings, you may want to reprocess existing data:

```bash
docker-compose exec horizon python -m horizon.cli.rebuild
```

See [Rebuild](09-rebuild.md) for details.

## Troubleshooting

### Settings Not Taking Effect

1. Ensure you clicked **Save** in the web interface
2. Check browser console for errors
3. Verify container has write access to config directory

### Unexpected Classifications

1. Lower `commuter_threshold` to be more lenient
2. Increase `bucket_epsilon` to create broader patterns
3. Check `min_confidence` isn't filtering valid reads

### Too Many/Few Patterns

1. Adjust `bucket_epsilon` (higher = fewer patterns)
2. Adjust `min_bucket_samples` (higher = fewer patterns)
3. Review `min_confidence` (lower = more data)
