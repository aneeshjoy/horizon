# Pattern Detection

Horizon uses a bucket-based clustering system to detect recurring vehicle visitation patterns.

## How It Works

### The Bucket System

Each vehicle maintains "buckets" representing identified patterns:

```json
{
  "ABC-123": {
    "buckets": [
      {
        "avg_minutes": 510,        // 8:30 AM (510 minutes from midnight)
        "days_seen": [0, 1, 2, 3, 4],  // Monday-Friday
        "count": 12,               // 12 sightings in this pattern
        "confidence_scores": [0.92, 0.89, 0.95, ...],
        "last_updated": "2026-03-15T08:30:15"
      },
      {
        "avg_minutes": 1020,       // 5:00 PM
        "days_seen": [0, 1, 2, 3, 4],
        "count": 10,
        "confidence_scores": [0.88, 0.91, ...],
        "last_updated": "2026-03-15T17:00:22"
      }
    ],
    "pending": [
      {
        "minutes": 720,            // 12:00 PM
        "day_of_week": 2,          // Wednesday
        "confidence": 0.75,
        "timestamp": "2026-03-15T12:00:00"
      }
    ]
  }
}
```

### Pattern Detection Flow

```
New Reading Arrives
        ↓
    OCR Correction
        ↓
  Confidence Filter
   (skip if < 65%)
        ↓
   Extract Time/Day
        ↓
   Check Existing Buckets
        ↓
    ┌───┴───┐
    │       │
  Match?   No Match
    │       │
    │       ↓
    │    Add to Pending
    │       │
    │       ↓
    │   3+ Pending at
    │   similar time?
    │       │
    │    ┌──┴──┐
    │    │     │
    │   Yes   No
    │    │     │
    │    ↓     │
    │ New      │
    │ Bucket   │
    │          │
    └──────────┘
       Save to
    JSON storage
```

### Matching Logic

A reading matches a bucket if:

1. **Time Match**: Reading time is within ±45 minutes of bucket average
2. **Update**: If matched, bucket average adjusts slightly toward new reading

**Example**:
```
Bucket: 8:00 AM (avg)
Reading at 8:30 AM → Match (30 min diff) → Update bucket to ~8:05 AM
Reading at 9:00 AM → No match (60 min diff) → Add to pending
```

### New Bucket Creation

When 3+ pending readings cluster at similar times:
1. Calculate average time
2. Identify common days
3. Create new bucket
4. Move readings from pending to new bucket

**Example**:
```
Pending readings:
- Mon 12:15 PM
- Tue 12:20 PM
- Wed 12:10 PM

→ Creates new bucket: 12:15 PM (Mon-Wed)
```

## Configuration

### Bucket Epsilon

Time tolerance for matching readings to buckets.

**Default**: 45 minutes

| Setting | Effect |
|---------|--------|
| 30 min | More precise patterns, more buckets |
| 45 min | Balanced (default) |
| 60-90 min | Fewer, broader patterns |

### Minimum Bucket Samples

Readings required to create a new pattern.

**Default**: 3

| Setting | Effect |
|---------|--------|
| 2 | Faster detection, more false patterns |
| 3 | Balanced (default) |
| 4-5 | Slower detection, fewer false patterns |

## Pattern Examples

### Commuter Vehicle

```
Vehicle: RESIDENT-001

Buckets:
├── 07:45 AM (Mon-Fri) - 15 sightings
│   → Morning commute pattern
├── 05:30 PM (Mon-Fri) - 14 sightings
│   → Evening commute pattern
└── 12:30 PM (Mon-Fri) - 6 sightings
    → Occasional lunch return

Classification: Commuter (RDS: 85%)
```

### Delivery Vehicle

```
Vehicle: DELIVERY-123

Buckets:
├── 09:15 AM (Mon-Fri) - 8 sightings
│   → Morning deliveries
├── 02:30 PM (Mon, Wed, Fri) - 5 sightings
│   → Afternoon deliveries (3x/week)
└── 11:00 AM (Tue, Thu) - 3 sightings
    → Mid-week deliveries

Classification: Commuter (RDS: 72%)
```

### Suspicious Vehicle

```
Vehicle: UNKNOWN-999

Buckets:
├── 11:45 PM (Fri, Sat) - 3 sightings
│   → Late night weekends
└── Pending: 7 readings at scattered times
    → No clear pattern

Classification: Suspicious (RDS: 25%)
```

## Visualizing Patterns

The web interface displays patterns as:

### Pattern Grid

- Rows: Days of week (Mon-Sun)
- Columns: Time of day (45-minute buckets)
- Color intensity: Number of sightings
- Hover: View details for each bucket

### Pattern List

Text-based view showing:
- Average time
- Days seen
- Number of sightings
- Confidence range

## Pattern Statistics

For each vehicle, the system tracks:

| Statistic | Description |
|-----------|-------------|
| Total sightings | All recorded detections |
| Pattern count | Number of identified patterns |
| Pending count | Unclassified readings awaiting pattern |
| First seen | Initial detection timestamp |
| Last seen | Most recent detection |
| Average confidence | Mean detection confidence |

## Debugging Patterns

### Why No Patterns Detected?

1. **Insufficient data**: Need 3+ readings at similar times
2. **High variance**: Readings too scattered (increase `bucket_epsilon`)
3. **Low confidence**: Reads filtered out (lower `min_confidence`)

### Why Too Many Patterns?

1. **Tight tolerance**: Decrease `bucket_epsilon`
2. **High sensitivity**: Increase `min_bucket_samples`
3. **OCR noise**: Ensure `ocr_similarity_threshold` is appropriate

### Why Unexpected Times?

1. **Timezone issues**: Verify Frigate and Horizon use same timezone
2. **Clock drift**: Check system time sync
3. **Daylight saving**: Some readings may shift by 1 hour

## Best Practices

1. **Start with defaults**: 45 min epsilon, 3 min samples work for most cases
2. **Let data accumulate**: Patterns need 3-7 days to stabilize
3. **Review pending**: Check pending readings weekly for new patterns
4. **Adjust gradually**: Change one setting at a time
5. **Rebuild after changes**: Reprocess data with new settings (see [Rebuild](09-rebuild.md))

## Performance

Pattern detection is fast:
- **Per reading**: ~9ms (110 readings/second)
- **Query**: ~1ms per vehicle
- **Storage**: ~200KB for 1000 vehicles with patterns
