"""
Extract License Plate Data from Frigate Database
Reads from frigate.db and writes to frigate_events.jsonl
"""

import sqlite3
import json
import os
from datetime import datetime

# Settings
DEFAULT_FRIGATE_DB = "data/external/frigate.db"
DEFAULT_OUTPUT_JSONL = "data/raw/frigate_events.jsonl"

def _get_frigate_db():
    """Get the Frigate database path, configurable via environment variable."""
    return os.environ.get("HORIZON_FRIGATE_DB", DEFAULT_FRIGATE_DB)

def _get_output_jsonl():
    """Get the output JSONL path, configurable via environment variable."""
    return os.environ.get("HORIZON_EVENTS_FILE", DEFAULT_OUTPUT_JSONL)

def query_frigate_plates(db_path, limit=None):
    """
    Extract license plate detections from Frigate database.

    Frigate schema:
    - events: has timestamp, camera, labels, data (JSON)
    - data column contains: recognized_license_plate, recognized_license_plate_score

    Returns list of tuples: (timestamp, camera, plate, confidence, name)
    """

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Make sure you've copied your frigate.db here first!")
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check available tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {', '.join(tables)}\n")

        # Method 1: Frigate standard schema - event table with JSON data
        if 'event' in tables:
            print("Querying from event table with recognized_license_plate data...")

            query = """
            SELECT
                id,
                start_time,
                camera,
                data
            FROM event
            WHERE label = 'license_plate'
            AND data IS NOT NULL
            ORDER BY start_time DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            results = cursor.fetchall()

            plates = []
            for row in results:
                start_time = row[1]
                camera = row[2]

                # Extract plate and confidence from JSON data field
                try:
                    data = json.loads(row[3]) if row[3] else {}
                    plate = data.get('recognized_license_plate', 'UNKNOWN')
                    confidence = float(data.get('recognized_license_plate_score', 0.5))
                    # Try to get name from Frigate's additional_data or similar
                    name = data.get('sub_label') or data.get('name') or None
                except:
                    plate = 'UNKNOWN'
                    confidence = 0.5
                    name = None

                plates.append({
                    'timestamp': start_time,
                    'camera': camera,
                    'plate': plate,
                    'confidence': confidence,
                    'name': name
                })

            conn.close()
            print(f"✓ Successfully extracted {len(plates)} detections\n")
            return plates

        # Method 2: Look for plate_detections table
        if 'plate_detections' in tables:
            print("Found 'plate_detections' table")
            cursor.execute("""
                SELECT timestamp, camera, plate, confidence, name
                FROM plate_detections
                WHERE plate IS NOT NULL AND confidence > 0.5
                ORDER BY timestamp DESC
            """)
            if limit:
                results = cursor.fetchmany(limit)
            else:
                results = cursor.fetchall()

            plates = [(dict(row)) for row in results]
            conn.close()
            return plates

        # Method 3: Look in event_detections with lightning plates
        if 'event_detections' in tables and 'events' in tables:
            print("Querying from event_detections and events tables...")

            query = """
            SELECT
                e.timestamp,
                e.camera,
                ed.label,
                ed.confidence,
                ed.data
            FROM event_detections ed
            JOIN events e ON ed.event_id = e.id
            WHERE ed.label = 'license_plate'
            AND ed.confidence > 0.5
            ORDER BY e.timestamp DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            results = cursor.fetchall()

            plates = []
            for row in results:
                timestamp = row[0]
                camera = row[1]
                confidence = row[3]

                # Extract plate and name from JSON data field
                try:
                    data = json.loads(row[4]) if row[4] else {}
                    plate = data.get('plate') or data.get('text') or data.get('license_plate') or 'UNKNOWN'
                    name = data.get('name') or data.get('sub_label') or None
                except:
                    plate = 'UNKNOWN'
                    name = None

                plates.append({
                    'timestamp': timestamp,
                    'camera': camera,
                    'plate': plate,
                    'confidence': confidence,
                    'name': name
                })

            conn.close()
            return plates

        # Method 4: Look for any table with 'plate' in name
        plate_tables = [t for t in tables if 'plate' in t.lower()]
        if plate_tables:
            print(f"Found potential plate tables: {plate_tables}")
            table = plate_tables[0]
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [(row[1]) for row in cursor.fetchall()]
            print(f"Columns in {table}: {columns}\n")

        print("Warning: Could not find license plate data in expected schema")
        print("Available tables:", tables)

        conn.close()
        return []

    except Exception as e:
        print(f"Database error: {e}")
        return []

def export_to_jsonl(plates, output_file):
    """Export extracted plates to JSONL format (one JSON object per line)"""

    if not plates:
        print("No plates to export")
        return 0

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for plate_data in plates:
            # Parse timestamp
            try:
                if isinstance(plate_data['timestamp'], str):
                    dt = datetime.fromisoformat(plate_data['timestamp'].replace('Z', '+00:00'))
                else:
                    dt = datetime.fromtimestamp(plate_data['timestamp'])
                unix_timestamp = dt.timestamp()
            except:
                print(f"Warning: Could not parse timestamp {plate_data['timestamp']}")
                continue

            plate = plate_data.get('plate', 'UNKNOWN').strip()
            confidence = float(plate_data.get('confidence', 0.5))
            camera = plate_data.get('camera', 'unknown')
            name = plate_data.get('name')  # May be None

            # Create event object
            event = {
                'timestamp': unix_timestamp,
                'plate': plate,
                'score': confidence,
                'camera': camera,
                'id': f"frigate-{unix_timestamp}-{camera}",  # Generate unique ID
                'name': name
            }

            # Write as JSON line
            f.write(json.dumps(event, separators=(',', ':')) + '\n')
            count += 1

    return count

def main():
    print("=" * 70)
    print("FRIGATE LICENSE PLATE DATA EXTRACTOR")
    print("=" * 70)

    frigate_db = _get_frigate_db()
    output_jsonl = _get_output_jsonl()

    # Step 1: Extract from database
    print("\n[Step 1] Extracting plates from Frigate database...")
    print("-" * 70)

    plates = query_frigate_plates(frigate_db)

    if not plates:
        print("\n❌ No license plate data found in database")
        print("\nTroubleshooting:")
        print("1. Make sure you've copied frigate.db to data/external/")
        print("2. Your Frigate instance must have detected license plates")
        print("3. Check the database schema matches expected format")
        return

    print(f"✓ Found {len(plates)} license plate detections")

    # Step 2: Export to JSONL
    print("\n[Step 2] Exporting to JSONL format...")
    print("-" * 70)

    count = export_to_jsonl(plates, output_jsonl)
    print(f"✓ Exported {count} readings to {output_jsonl}")

    print("\n" + "=" * 70)
    print("✓ EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"\nRaw events saved to: {output_jsonl}")
    print(f"Run the rebuild operation to update plate_profiles.json")

if __name__ == "__main__":
    main()
