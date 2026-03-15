"""
Frigate Database Inspector & Safe Copy Helper
Helps you understand your Frigate database schema and safely export data
"""

import sqlite3
import os
import shutil
from datetime import datetime

def inspect_frigate_db(db_path):
    """Inspect Frigate database schema and show statistics"""
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "=" * 70)
        print("FRIGATE DATABASE INSPECTION")
        print("=" * 70)
        print(f"Database: {db_path}")
        print(f"Size: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
        print(f"Modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\nTables ({len(tables)}):")
        print("-" * 70)
        
        for table_name in tables:
            table = table_name[0]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            print(f"\n📊 {table} ({count} rows)")
            print(f"   Columns: {', '.join([col[1] for col in columns])}")
            
            # Show sample data for relevant tables
            if any(x in table.lower() for x in ['plate', 'detection', 'event']):
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"   Sample: {sample}")
        
        # Search for license plate tables specifically
        print("\n" + "=" * 70)
        print("SEARCHING FOR LICENSE PLATE DATA")
        print("=" * 70)
        
        plate_tables = [t[0] for t in tables if 'plate' in t[0].lower()]
        
        if plate_tables:
            print(f"\n✓ Found {len(plate_tables)} plate-related table(s):")
            for table in plate_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} rows")
        else:
            print("\n⚠ No obvious plate tables found")
            print("  License plates may be stored in:")
            print("  - events (with label='license_plate')")
            print("  - event_detections (with label='license_plate')")
        
        # Check for relevant columns
        print("\nSearching for columns with 'plate' or 'detection'...")
        for table_name in tables:
            table = table_name[0]
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            relevant_cols = [col for col in columns if any(x in col[1].lower() for x in ['plate', 'detect', 'confidence'])]
            if relevant_cols:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"\n  {table} ({count} rows):")
                for col in relevant_cols:
                    print(f"    - {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error inspecting database: {e}")

def safe_copy_database(source_db, dest_db):
    """
    Safely copy Frigate database without interfering with running Frigate.
    """
    
    print("\n" + "=" * 70)
    print("SAFE DATABASE COPY")
    print("=" * 70)
    
    if not os.path.exists(source_db):
        print(f"❌ Source database not found: {source_db}")
        print("\nCommon locations:")
        print("  Docker: /path/to/frigate/storage/frigate.db")
        print("  Home Assistant: /config/frigate/storage/frigate.db")
        print("  Standalone: ~/.frigate/frigate.db or /var/lib/frigate/frigate.db")
        return False
    
    if os.path.exists(dest_db):
        print(f"⚠ Destination already exists: {dest_db}")
        response = input("Overwrite? (y/n): ").lower()
        if response != 'y':
            print("Cancelled")
            return False
    
    try:
        print(f"\nCopying from: {source_db}")
        print(f"Copying to:   {dest_db}")
        
        # Use shutil for safe copy
        shutil.copy2(source_db, dest_db)
        
        # Verify
        if os.path.exists(dest_db):
            source_size = os.path.getsize(source_db) / 1024 / 1024
            dest_size = os.path.getsize(dest_db) / 1024 / 1024
            
            if abs(source_size - dest_size) < 0.1:  # Within 100KB
                print(f"✓ Copy successful ({dest_size:.2f} MB)")
                return True
            else:
                print(f"⚠ Size mismatch!")
                print(f"  Source: {source_size:.2f} MB")
                print(f"  Dest:   {dest_size:.2f} MB")
                return False
        
    except Exception as e:
        print(f"❌ Copy failed: {e}")
        return False

def check_license_plate_data(db_path):
    """Check if database contains any license plate data"""
    
    if not os.path.exists(db_path):
        return False, 0
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Method 1: Check for plate_detections table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plate_detections'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM plate_detections WHERE plate IS NOT NULL AND confidence > 0.5")
            count = cursor.fetchone()[0]
            if count > 0:
                conn.close()
                return True, count
        
        # Method 2: Check event_detections with license_plate label
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event_detections'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT COUNT(*) FROM event_detections 
                WHERE label = 'license_plate' AND confidence > 0.5
            """)
            count = cursor.fetchone()[0]
            if count > 0:
                conn.close()
                return True, count
        
        conn.close()
        return False, 0
        
    except:
        return False, 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Frigate Database Inspector")
    parser.add_argument('--inspect', help='Inspect database', metavar='PATH')
    parser.add_argument('--copy', help='Copy database from source to dest', nargs=2, metavar=('SRC', 'DEST'))
    parser.add_argument('--check', help='Check for license plate data', metavar='PATH')
    
    args = parser.parse_args()
    
    if args.inspect:
        inspect_frigate_db(args.inspect)
    elif args.copy:
        safe_copy_database(args.copy[0], args.copy[1])
    elif args.check:
        has_data, count = check_license_plate_data(args.check)
        if has_data:
            print(f"✓ Database contains {count} license plate detections")
        else:
            print(f"✗ No license plate data found")
    else:
        # Default: inspect frigate.db in current directory
        if os.path.exists('frigate.db'):
            inspect_frigate_db('frigate.db')
        else:
            print("No frigate.db found in current directory")
            print("\nUsage:")
            print("  python3 inspect_frigate_db.py --inspect /path/to/frigate.db")
            print("  python3 inspect_frigate_db.py --copy /source/frigate.db ./frigate.db")
            print("  python3 inspect_frigate_db.py --check /path/to/frigate.db")

if __name__ == "__main__":
    main()
