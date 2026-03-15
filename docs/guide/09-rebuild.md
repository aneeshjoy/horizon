# Rebuild

Rebuilding reprocesses all historical data with current configuration settings. Use this after changing pattern detection or classification settings.

## What Rebuild Does

Reprocessing flow:
```
1. Load raw readings (historical data)
2. Clear existing patterns/buckets
3. Re-process each reading with new settings
4. Re-detect all patterns
5. Re-classify all vehicles
6. Save updated profiles
```

## When to Rebuild

### Pattern Detection Changes

After changing:
- `bucket_epsilon` - Time tolerance for matching
- `min_bucket_samples` - Minimum readings for new pattern
- `min_confidence` - Confidence filtering threshold

### Classification Changes

After changing:
- `commuter_threshold` - RDS threshold for Commuter
- `unknown_threshold` - RDS threshold for Unknown
- Classification weights

### OCR Settings

After changing:
- `ocr_similarity_threshold` - Fuzzy matching threshold

### Other Scenarios

- After importing new historical data
- After database corruption or errors
- To reset all patterns
- Testing configuration changes

## Running Rebuild

### Via Web Interface

1. Navigate to http://localhost:8001
2. Go to **Configuration**
3. Click **Rebuild All Data**
4. Confirm and monitor progress

## What Data is Used

Rebuild uses stored raw readings from previous imports:
- CSV exports from Frigate database
- MQTT event logs
- Historical data files

**Important**: If you don't have historical data stored, rebuild will have nothing to process.

## Rebuild Process

### Phase 1: Preparation

```
Loading historical data...
Found 1,247 readings from 3 sources
```

### Phase 2: Processing

```
Processing readings...
[████████████████████░░] 90% (1123/1247)
```

### Phase 3: Pattern Detection

```
Detecting patterns...
Found 203 patterns across 127 vehicles
```

### Phase 4: Classification

```
Classifying vehicles...
Commuter: 89 vehicles
Unknown: 31 vehicles
Suspicious: 7 vehicles
```

### Phase 5: Completion

```
Rebuild complete!
Total time: 4.2 seconds
Vehicles processed: 127
Patterns detected: 203
```

## Performance

| Data Size | Rebuild Time |
|-----------|--------------|
| 100 readings | ~1 second |
| 1,000 readings | ~3 seconds |
| 10,000 readings | ~25 seconds |
| 100,000 readings | ~4 minutes |

## Before Rebuilding

### 1. Backup Current Profiles

```bash
cp data/processed/plate_profiles.json data/processed/plate_profiles.json.backup
```

### 2. Note Current Settings

Screenshot or note your current configuration.

### 3. Check Historical Data Availability

Ensure you have:
- Original Frigate database
- Exported CSV files
- MQTT event logs (if applicable)

## After Rebuilding

### 1. Verify Pattern Count

Should see different patterns with new settings.

### 2. Check Classification Distribution

May see different vehicle classifications.

### 3. Compare Before/After

| Metric | Before | After |
|--------|--------|-------|
| Total patterns | 203 | 156 |
| Commuter vehicles | 89 | 76 |
| Unknown vehicles | 31 | 45 |
| Suspicious vehicles | 7 | 6 |

## Troubleshooting

### "No historical data found"

**Cause**: No raw readings stored from previous imports

**Solution**: Re-import from Frigate database first (see [Data Import](08-data-import.md))

### Rebuild Takes Too Long

**Solutions**:
1. Reduce historical data (remove old exports)
2. Process in batches (specific date ranges)
3. Increase system resources

### Unexpected Results After Rebuild

**Causes**:
1. Configuration settings very different
2. Data quality issues

**Solutions**:
1. Review configuration changes
2. Restore from backup if needed
3. Adjust settings incrementally

### Patterns Disappeared

**Causes**:
1. `bucket_epsilon` too small (patterns split)
2. `min_bucket_samples` too high (insufficient data)
3. `min_confidence` too high (data filtered)

**Solutions**:
1. Increase `bucket_epsilon`
2. Decrease `min_bucket_samples`
3. Decrease `min_confidence`

## Best Practices

1. **Backup first**: Always backup before rebuilding
2. **Test changes**: Make small config changes, rebuild, review
3. **Compare results**: Note pattern/classification changes
4. **Document settings**: Keep record of working configurations
5. **Schedule rebuilds**: Rebuild after significant config changes

## Rebuild vs Fresh Import

| Feature | Rebuild | Fresh Import |
|---------|---------|--------------|
| Data source | Stored readings | Frigate database |
| Speed | Fast (local data) | Slower (database query) |
| Use case | Config changes | New installation |

**Use Rebuild** when:
- Changing configuration
- Testing settings
- Reprocessing existing data

**Use Fresh Import** when:
- First-time setup
- Adding new Frigate data
- No stored readings available

## Example Workflow

```
1. Current config: bucket_epsilon = 45
2. Change to: bucket_epsilon = 60
3. Backup profiles
4. Run rebuild
5. Review results:
   - Fewer patterns (expected with larger epsilon)
   - Same vehicles reclassified
6. If unsatisfied, restore backup and try different value
```

## Related Topics

- [Configuration](04-configuration.md) - Settings that require rebuild
- [Pattern Detection](05-pattern-detection.md) - How patterns are detected
- [Classification](06-classification.md) - How vehicles are classified
- [Data Import](08-data-import.md) - Importing new data
