# Architecture

## System Overview

Horizon is a Python-based system with a React web interface. It processes license plate readings to detect patterns and classify vehicle behavior.

```
┌─────────────────┐
│   Frigate NVR   │
│  (LPR Camera)   │
└────────┬────────┘
         │
    MQTT / Database
         │
         ▼
┌─────────────────────────────────┐
│         Horizon Core            │
│  ┌───────────────────────────┐  │
│  │  Incremental Processor    │  │
│  │  - OCR correction         │  │
│  │  - Confidence filtering   │  │
│  │  - Bucket clustering      │  │
│  └───────────┬───────────────┘  │
│              │                   │
│  ┌───────────▼───────────────┐  │
│  │   Pattern Detection       │  │
│  │   - Bucket management     │  │
│  │   - Pattern extraction    │  │
│  └───────────┬───────────────┘  │
│              │                   │
│  ┌───────────▼───────────────┐  │
│  │  Classification Engine    │  │
│  │  - RDS scoring            │  │
│  │  - Category assignment    │  │
│  └───────────┬───────────────┘  │
└──────────────┼───────────────────┘
               │
               ▼
       ┌───────────────┐
       │ JSON Storage  │
       │   Profiles    │
       └───────────────┘
               │
               ▼
┌─────────────────────────────────┐
│      Web Interface (React)      │
│  - Vehicle search               │
│  - Pattern visualization        │
│  - Configuration                │
│  - Data export                  │
└─────────────────────────────────┘
```

## Data Flow

### 1. License Plate Reading Arrives

From Frigate via MQTT or database import:
```json
{
  "plate": "ABC-123",
  "timestamp": "2026-03-15T08:30:00",
  "confidence": 0.92
}
```

### 2. Incremental Processing

```python
# OCR Correction
- Remove low-confidence characters (?)
- Fuzzy match against known plates (85% threshold)
- Correct to best match if found

# Confidence Filtering
- Skip readings below threshold (default 65%)
- Prevents false positives from poor OCR

# Time Processing
- Extract day of week (0-6)
- Convert time to minutes from midnight
```

### 3. Bucket Matching

Each vehicle has "buckets" representing identified patterns:

```python
{
  "avg_minutes": 510,      # 8:30 AM
  "days_seen": [0,1,2,3,4], # Mon-Fri
  "count": 12,              # 12 sightings
  "confidence_scores": [...]
}
```

**Matching Logic:**
- New reading within ±45 minutes of bucket average? → Update bucket
- Otherwise? → Add to pending pile
- 3+ pending readings at similar time? → Create new bucket

### 4. Pattern Storage

```json
{
  "ABC-123": {
    "buckets": [
      {"avg_minutes": 510, "days_seen": [0,1,2,3,4], "count": 12},
      {"avg_minutes": 1020, "days_seen": [0,1,2,3,4], "count": 10}
    ],
    "pending": [...],
    "first_seen": "2026-03-01T08:30:00",
    "last_seen": "2026-03-15T17:00:00",
    "total_readings": 24
  }
}
```

### 5. Classification

Routine Deviation Score (RDS) calculated from:
- **Pattern Adherence (40%)** - % of sightings matching patterns
- **Confidence Stability (30%)** - Consistency of confidence scores
- **Pattern Concentration (30%)** - How concentrated patterns are

| RDS Score | Classification |
|-----------|---------------|
| 80-100% | Commuter |
| 60-79% | Commuter |
| 40-59% | Unknown |
| 0-39% | Suspicious |

## Component Breakdown

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| Processor | `src/horizon/processor.py` | Bucket-based pattern detection |
| Analysis | `src/horizon/analysis.py` | Vehicle classification (RDS) |
| MQTT Service | `src/horizon/mqtt/` | Real-time processing |
| Import Service | `src/horizon/frigate/import_service.py` | Database import |
| Rebuild Service | `src/horizon/rebuild/rebuild_service.py` | Reprocess with new settings |

### Web Interface

| Component | Purpose |
|-----------|---------|
| FastAPI Backend | REST API, serves frontend |
| React Frontend | Pattern visualization, configuration |
| Pattern Grid | 45-minute bucket clustering visualization |
| Trend Charts | Historical analytics |
| Config Panel | Settings management |

## Performance Characteristics

| Operation | Time | Throughput |
|-----------|------|------------|
| Single reading | ~9ms | 110/sec |
| Vehicle query | ~1ms | - |
| Initial load (1000 vehicles) | ~5 sec | - |
| Storage | ~200KB | - |

## Scalability

- Designed for 1000+ vehicles
- O(1) bucket lookup per reading
- Lazy profile loading (not kept in RAM)
- Handles 100+ readings/second sustained
