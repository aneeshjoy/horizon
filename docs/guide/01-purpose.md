# Purpose

Horizon is a license plate pattern analysis system designed to work with [Frigate](https://github.com/blakeblackshear/frigate). It analyzes vehicle movement patterns over time to identify regular behaviors and flag suspicious activity.

## What It Does

Horizon processes license plate readings from Frigate and:

- **Detects patterns** - Identifies recurring visitation times (e.g., "weekday mornings")
- **Classifies vehicles** - Categorizes as Commuter, Unknown, or Suspicious based on routine adherence
- **Handles OCR noise** - Corrects common license plate recognition errors
- **Processes in real-time** - Handles ~110 readings/second
- **Provides a web interface** - Modern UI for exploring vehicle patterns

## Use Cases

- **Residential security** - Identify regular visitors vs. unknown vehicles
- **Parking analysis** - Understand peak usage times and patterns
- **Access control** - Automate decisions based on vehicle behavior
- **Suspicious activity detection** - Flag vehicles with irregular visitation patterns

## How It Works With Frigate

```
Frigate detects license plate
        ↓
   MQTT or Database
        ↓
   Horizon processes
        ↓
   Pattern detected
        ↓
   Classification assigned
```

Horizon consumes license plate data from Frigate through two methods:
- **Import** - Extract historical data from Frigate database
- **MQTT** - Process detections in real-time as they occur

## Key Features

| Feature | Description |
|---------|-------------|
| Real-time processing | ~9ms per reading, 110 readings/second |
| OCR correction | Fuzzy matching handles noisy reads |
| Pattern detection | Bucket-based clustering (45min tolerance) |
| Vehicle classification | Routine Deviation Score (RDS) 0-100% |
| Web interface | React-based UI with dark/light themes |
| Data export | PDF, CSV, JSON export options |
| Rebuild capability | Reprocess all data with new settings |
