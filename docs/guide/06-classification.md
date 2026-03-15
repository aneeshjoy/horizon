# Classification

Horizon classifies vehicles based on how predictable their patterns are. This helps identify regular visitors vs. suspicious activity.

## Routine Deviation Score (RDS)

Every vehicle receives an RDS score from 0-100%:

| RDS Score | Classification | Description |
|-----------|---------------|-------------|
| 80-100% | Commuter | Highly predictable patterns |
| 60-79% | Commuter | Regular with some variation |
| 40-59% | Unknown | Inconsistent behavior |
| 0-39% | Suspicious | Highly erratic |

## How RDS is Calculated

RDS is a weighted score from three components:

```
RDS = (Pattern Adherence × 40%) + (Confidence Stability × 30%) + (Pattern Concentration × 30%)
```

### 1. Pattern Adherence (40%)

**What it measures**: Percentage of sightings that match identified patterns

**Calculation**:
```
Pattern Adherence = (Readings in Buckets) / (Total Readings) × 100
```

**Example**:
```
Vehicle: 24 total sightings
├── 20 in patterns (buckets)
└── 4 pending (unclassified)

Pattern Adherence = 20/24 × 100 = 83%
Score component = 83 × 0.40 = 33.2
```

### 2. Confidence Stability (30%)

**What it measures**: Consistency of detection confidence scores

**Calculation**:
```
Confidence Stability = (Average Confidence) - (Standard Deviation)
```

**Example**:
```
Confidence scores: [0.92, 0.89, 0.95, 0.91, 0.93]
Average: 0.92
Std Dev: 0.02
Confidence Stability = 0.92 - 0.02 = 0.90 (90%)
Score component = 90 × 0.30 = 27.0
```

### 3. Pattern Concentration (30%)

**What it measures**: How concentrated sightings are in few patterns

**Calculation**: Uses Herfindahl-Hirschman Index (HHI)

```
Pattern Concentration = Sum(Pattern Proportion²)
```

**Example**:
```
Total sightings: 20
Pattern 1: 12 sightings (60%)
Pattern 2: 6 sightings (30%)
Pattern 3: 2 sightings (10%)

Concentration = 0.60² + 0.30² + 0.10²
             = 0.36 + 0.09 + 0.01
             = 0.46 (46%)
Score component = 46 × 0.30 = 13.8
```

**Higher concentration** = Most sightings in one pattern (good)
**Lower concentration** = Sightings scattered across many patterns (bad)

### Final RDS Score

```
RDS = 33.2 + 27.0 + 13.8 = 74%
Classification: Commuter
```

## Classification Examples

### Example 1: Regular Commuter

```
Vehicle: RESIDENT-001

Data:
- 30 total sightings
- 28 in patterns (93%)
- 2 pending
- Confidence: 0.92 avg, 0.03 std dev
- 2 patterns: morning (18), evening (12)

Calculation:
- Pattern Adherence: 28/30 × 100 × 0.40 = 37.3
- Confidence Stability: (0.92 - 0.03) × 100 × 0.30 = 26.7
- Pattern Concentration: 0.62 × 100 × 0.30 = 18.6

RDS = 37.3 + 26.7 + 18.6 = 82.6%
Classification: Commuter ✓
```

### Example 2: Inconsistent Vehicle

```
Vehicle: UNKNOWN-456

Data:
- 20 total sightings
- 12 in patterns (60%)
- 8 pending
- Confidence: 0.78 avg, 0.15 std dev
- 4 patterns: 3-4 sightings each

Calculation:
- Pattern Adherence: 12/20 × 100 × 0.40 = 24.0
- Confidence Stability: (0.78 - 0.15) × 100 × 0.30 = 18.9
- Pattern Concentration: 0.35 × 100 × 0.30 = 10.5

RDS = 24.0 + 18.9 + 10.5 = 53.4%
Classification: Unknown
```

### Example 3: Suspicious Vehicle

```
Vehicle: STRANGER-999

Data:
- 15 total sightings
- 4 in patterns (27%)
- 11 pending
- Confidence: 0.65 avg, 0.20 std dev
- 1 pattern: 4 sightings at random times

Calculation:
- Pattern Adherence: 4/15 × 100 × 0.40 = 10.7
- Confidence Stability: (0.65 - 0.20) × 100 × 0.30 = 13.5
- Pattern Concentration: 0.27 × 100 × 0.30 = 8.1

RDS = 10.7 + 13.5 + 8.1 = 32.3%
Classification: Suspicious
```

## Configuring Classification

### Threshold Adjustment

Adjust when vehicles fall into each category:

```yaml
# Default
commuter_threshold: 60    # RDS ≥ 60% = Commuter
unknown_threshold: 40     # RDS 40-59% = Unknown

# More strict - harder to be "Commuter"
commuter_threshold: 70    # RDS ≥ 70% = Commuter
unknown_threshold: 50     # RDS 50-69% = Unknown

# More lenient - easier to be "Commuter"
commuter_threshold: 50    # RDS ≥ 50% = Commuter
unknown_threshold: 30     # RDS 30-49% = Unknown
```

### Weight Adjustment

Change how much each component affects the score:

```yaml
# Default (balanced)
pattern_adherence_weight: 40
confidence_stability_weight: 30
pattern_concentration_weight: 30

# Focus on pattern matching (ignore confidence variance)
pattern_adherence_weight: 60
confidence_stability_weight: 10
pattern_concentration_weight: 30

# Focus on consistent detections
pattern_adherence_weight: 30
confidence_stability_weight: 50
pattern_concentration_weight: 20
```

**Important**: Weights must sum to 100

## When to Adjust Classification

### Too Many "Suspicious" Vehicles

**Problem**: Legitimate vehicles flagged as suspicious

**Solutions**:
1. Lower `commuter_threshold` to 50%
2. Lower `unknown_threshold` to 30%
3. Increase `pattern_adherence_weight` to 50%
4. Increase `bucket_epsilon` to create broader patterns

### Too Many "Commuter" Vehicles

**Problem**: Suspicious vehicles not being caught

**Solutions**:
1. Raise `commuter_threshold` to 70%
2. Raise `unknown_threshold` to 50%
3. Decrease `bucket_epsilon` for more precise patterns
4. Increase `min_confidence` to filter low-quality reads

### Too Many "Unknown" Vehicles

**Problem**: Vehicles not being classified

**Solutions**:
1. Wait for more data (need 3+ readings per pattern)
2. Decrease `min_bucket_samples` to 2
3. Widen thresholds (above)
4. Check if `min_confidence` is too high

## Viewing Classification

### Web Interface

1. Navigate to http://localhost:8000
2. Search for a vehicle
3. View classification badge and RDS score

### Classification Badge Colors

| Classification | Color |
|---------------|-------|
| Commuter | Green |
| Unknown | Yellow |
| Suspicious | Red |

## Classification Limitations

### Cold Start Problem

Vehicles need 3+ readings to form any pattern. Until then:
- Classification shows "Unknown" or "Insufficient data"
- More sightings needed for accurate classification

### Time Variations

Vehicles with legitimate schedule changes may show lower RDS:
- Shift workers
- Irregular visitors
- New residents (still learning patterns)

### Environmental Factors

External conditions affect classification:
- Weather affects camera quality → lower confidence
- Seasonal schedule changes → pattern shifts
- Camera angle changes → different detection patterns

## Best Practices

1. **Wait for stability**: Give new vehicles 1-2 weeks before evaluating classification
2. **Review "Unknown" weekly**: Check if patterns are emerging
3. **Monitor "Suspicious" alerts**: Investigate but allow for legitimate variation
4. **Adjust gradually**: Change thresholds one at a time
5. **Consider context**: Some locations naturally have more irregular traffic

## Rebuilding Classifications

After changing classification settings, rebuild to reclassify all vehicles:

```bash
docker-compose exec horizon python -m horizon.cli.rebuild
```

See [Rebuild](09-rebuild.md) for details.
