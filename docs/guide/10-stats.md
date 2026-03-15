# Stats

Horizon tracks various statistics about vehicle patterns and system performance.

## System Statistics

View in web interface at http://localhost:8000

### Overview Stats

| Metric | Description |
|--------|-------------|
| Total vehicles | Unique license plates tracked |
| Total readings | All license plate detections processed |
| Total patterns | Identified visitation patterns |
| Commuter vehicles | Vehicles with RDS ≥ 60% |
| Unknown vehicles | Vehicles with RDS 40-59% |
| Suspicious vehicles | Vehicles with RDS < 40% |

## Vehicle Statistics

For each vehicle, the following is tracked:

### Basic Stats

```
Plate: ABC-123
First seen: 2026-03-01 08:30:00
Last seen: 2026-03-15 17:00:00
Total readings: 24
```

### Pattern Stats

```
Patterns identified: 2

Pattern 0:
  Time: 08:15 AM
  Days: Mon, Tue, Wed, Thu, Fri
  Sightings: 12
  Confidence: 0.89-0.95 (avg: 0.92)

Pattern 1:
  Time: 05:30 PM
  Days: Mon, Tue, Wed, Thu, Fri
  Sightings: 10
  Confidence: 0.85-0.93 (avg: 0.88)
```

### Classification Stats

```
Classification: Commuter
RDS Score: 85%

Breakdown:
  Pattern Adherence: 92% × 40% = 36.8
  Confidence Stability: 88% × 30% = 26.4
  Pattern Concentration: 73% × 30% = 21.9
```

## Pattern Statistics

### Time Distribution

```
Time Range    Sightings
00:00-06:00        2     (8%)
06:00-12:00       12     (50%)
12:00-18:00        8     (33%)
18:00-24:00        2     (8%)
```

### Day Distribution

```
Day        Sightings
Monday          5
Tuesday         4
Wednesday       5
Thursday        4
Friday          6
Saturday        0
Sunday          0
```

## Processing Statistics

### MQTT Processing (if enabled)

```
Messages received: 1,247
Readings processed: 1,198
Readings filtered: 49 (low confidence)
Patterns updated: 156
New patterns: 47
Processing rate: 12.3 msg/sec
```

### Import Statistics

```
Database size: 145.3 MB
Detections found: 847
Readings imported: 798
Readings skipped: 49 (below confidence)
Vehicles created: 127
Patterns detected: 203
Import time: 4.2 seconds
```

## Performance Metrics

### Processing Speed

| Operation | Time | Rate |
|-----------|------|------|
| Single reading | 9ms | 110/sec |
| Vehicle query | 1ms | 1000/sec |
| Pattern lookup | <1ms | - |
| Profile save | 50ms | 20/sec |

### Storage

| Data Type | Size |
|-----------|------|
| Vehicle profiles | ~200KB (1000 vehicles) |
| Historical readings | ~1MB (10,000 readings) |
| Event logs | ~500KB (1000 events) |

### Memory

| Component | Memory |
|-----------|--------|
| Core processor | ~50MB |
| MQTT listener | ~30MB |
| Web interface | ~100MB |
| Total | ~200MB |

## Export Statistics

Data export includes statistics:

### CSV Export

```
Plate,Classification,RDS,Total Readings,Patterns,First Seen,Last Seen
ABC-123,Commuter,85,24,2,2026-03-01,2026-03-15
XYZ-789,Unknown,52,8,1,2026-03-05,2026-03-14
```

### JSON Export

```json
{
  "stats": {
    "total_vehicles": 127,
    "total_readings": 2476,
    "total_patterns": 203,
    "classifications": {
      "commuter": 89,
      "unknown": 31,
      "suspicious": 7
    }
  },
  "vehicles": [...]
}
```

### PDF Export

Formatted report with:
- Summary statistics
- Per-vehicle details
- Pattern visualizations
- Classification breakdown

## Viewing Stats

Navigate to:
- **Home**: System-wide statistics
- **Vehicle Details**: Per-vehicle statistics
- **Configuration**: Current settings and processing stats

## Interpreting Stats

### High "Suspicious" Count

**Possible causes**:
1. Genuine irregular activity
2. Classification thresholds too strict
3. Insufficient data (cold start problem)
4. Pattern detection settings too narrow

**Actions**:
- Review individual vehicles
- Adjust classification thresholds
- Lower `min_bucket_samples`
- Increase `bucket_epsilon`

### Low Pattern Count

**Possible causes**:
1. Insufficient data
2. High `min_confidence` filtering
3. High `min_bucket_samples` requirement
4. Low `bucket_epsilon` (patterns split)

**Actions**:
- Wait for more data
- Lower confidence threshold
- Reduce minimum samples
- Increase time tolerance

### High "Unknown" Count

**Possible causes**:
1. Insufficient data for classification
2. Inconsistent genuine behavior
3. Thresholds set too high

**Actions**:
- Monitor over time (may resolve with more data)
- Adjust classification thresholds
- Review individual vehicles

## Statistics Retention

- Vehicle profiles: Kept indefinitely
- MQTT event logs: 1000 most recent events
- Import history: Last 10 imports
- Processing stats: Real-time (not persisted)

## Related Topics

- [Pattern Detection](05-pattern-detection.md) - How patterns are created
- [Classification](06-classification.md) - How vehicles are classified
- [Web Interface](04-configuration.md) - Viewing stats in UI
