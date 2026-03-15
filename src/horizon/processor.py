import json
import os
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Settings
PROFILES_FILE = "data/processed/plate_profiles.json"
BUCKET_EPS = 45  # minutes - how close readings need to be to fit in same bucket
BUCKET_MIN_SAMPLES = 3  # how many readings to create a new bucket

def clean_plate_string(plate):
    """Remove OCR artifacts and normalize for matching"""
    return plate.replace('?', '').strip()

def similarity_score(a, b):
    """Calculate similarity between two plate strings"""
    a_clean = clean_plate_string(a)
    b_clean = clean_plate_string(b)
    return SequenceMatcher(None, a_clean, b_clean).ratio()

def correct_ocr_error(detected_plate, fuzzy_against=None):
    """Correct OCR errors using fuzzy matching"""
    if not detected_plate or '?' in detected_plate:
        return detected_plate
    
    if fuzzy_against is None:
        fuzzy_against = []
    
    best_match = detected_plate
    best_score = 0
    
    for ref_plate in fuzzy_against:
        score = similarity_score(detected_plate, ref_plate)
        if score > best_score:
            best_score = score
            best_match = ref_plate
    
    if best_score >= 0.85:
        return best_match
    
    return detected_plate

def load_profiles():
    """Load plate profiles from JSON file"""
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    """Save plate profiles to JSON file"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(PROFILES_FILE), exist_ok=True)
    with open(PROFILES_FILE, 'w') as f:
        json.dump(profiles, f, indent=2)

def minutes_from_midnight(time_str):
    """Convert HH:MM:SS to minutes from midnight"""
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 60 + minutes

def fits_bucket(reading_minutes, bucket, tolerance=BUCKET_EPS):
    """Check if a reading fits within an existing bucket"""
    bucket_avg = bucket['avg_minutes']
    return abs(reading_minutes - bucket_avg) <= tolerance

def update_bucket(bucket, reading_minutes, day_of_week, confidence):
    """Update bucket with new reading"""
    count = bucket['count']
    # Weighted average to give more weight to recent readings
    bucket['avg_minutes'] = int(
        (bucket['avg_minutes'] * 0.7 + reading_minutes * 0.3)
    )
    if day_of_week not in bucket['days_seen']:
        bucket['days_seen'].append(day_of_week)
    bucket['confidence_scores'].append(confidence)
    bucket['count'] += 1
    bucket['last_updated'] = datetime.now().isoformat()
    return bucket

def create_bucket_from_pending(pending_list):
    """Create a new bucket from pending readings"""
    if len(pending_list) < BUCKET_MIN_SAMPLES:
        return None
    
    avg_minutes = int(sum(p['minutes'] for p in pending_list) / len(pending_list))
    days = list(set(p['day_of_week'] for p in pending_list))
    confidences = [p['confidence'] for p in pending_list]
    
    bucket = {
        'avg_minutes': avg_minutes,
        'days_seen': sorted(days),
        'confidence_scores': confidences,
        'count': len(pending_list),
        'last_updated': datetime.now().isoformat()
    }
    
    return bucket

def process_reading(plate, date_str, time_str, confidence):
    """
    Process a single license plate reading incrementally.
    Returns the updated profiles and statistics.
    """
    profiles = load_profiles()
    
    # Correct OCR errors using known plates as reference
    all_known_plates = list(profiles.keys())
    corrected_plate = correct_ocr_error(plate, all_known_plates)
    
    # Filter by confidence
    if confidence < 0.65:
        return profiles, {'status': 'filtered', 'confidence': confidence}
    
    # Create actual reading timestamp from date and time
    reading_timestamp = datetime.strptime(f"{date_str}T{time_str}", '%Y-%m-%dT%H:%M:%S').isoformat()
    
    # Initialize profile if needed
    if corrected_plate not in profiles:
        profiles[corrected_plate] = {
            'buckets': [],
            'pending': [],
            'first_seen': reading_timestamp,
            'last_seen': reading_timestamp,
            'total_readings': 0
        }
    
    profile = profiles[corrected_plate]
    
    # Update first_seen and last_seen to track min/max timestamps
    first_seen = datetime.fromisoformat(profile['first_seen'])
    last_seen = datetime.fromisoformat(profile['last_seen'])
    current_reading = datetime.fromisoformat(reading_timestamp)
    
    if current_reading < first_seen:
        profile['first_seen'] = reading_timestamp
    if current_reading > last_seen:
        profile['last_seen'] = reading_timestamp
    
    # Extract time info
    reading_minutes = minutes_from_midnight(time_str)
    day_of_week = datetime.strptime(date_str, '%Y-%m-%d').weekday()
    
    # Try to fit into existing bucket
    for bucket in profile['buckets']:
        if fits_bucket(reading_minutes, bucket):
            update_bucket(bucket, reading_minutes, day_of_week, confidence)
            profile['total_readings'] += 1
            save_profiles(profiles)
            return profiles, {
                'status': 'added_to_bucket',
                'plate': corrected_plate,
                'bucket_avg': bucket['avg_minutes']
            }
    
    # Doesn't fit in existing bucket - add to pending
    profile['pending'].append({
        'minutes': reading_minutes,
        'day_of_week': day_of_week,
        'confidence': confidence,
        'timestamp': f"{date_str}T{time_str}"
    })
    
    # Check if pending readings form a new cluster
    if len(profile['pending']) >= BUCKET_MIN_SAMPLES:
        # Find readings that cluster together
        pending_sorted = sorted(profile['pending'], key=lambda x: x['minutes'])
        
        # Try to find a cluster of at least MIN_SAMPLES readings
        for i in range(len(pending_sorted) - BUCKET_MIN_SAMPLES + 1):
            cluster = pending_sorted[i:i + BUCKET_MIN_SAMPLES]
            time_range = cluster[-1]['minutes'] - cluster[0]['minutes']
            
            if time_range <= BUCKET_EPS:
                # Found a cluster! Create a new bucket
                new_bucket = create_bucket_from_pending(cluster)
                if new_bucket:
                    profile['buckets'].append(new_bucket)
                    # Remove these readings from pending
                    for reading in cluster:
                        profile['pending'].remove(reading)
                    
                    profile['total_readings'] += len(cluster)
                    save_profiles(profiles)
                    return profiles, {
                        'status': 'created_new_bucket',
                        'plate': corrected_plate,
                        'bucket_avg': new_bucket['avg_minutes'],
                        'readings_used': len(cluster)
                    }
    
    # Just added to pending
    profile['total_readings'] += 1
    save_profiles(profiles)
    
    return profiles, {
        'status': 'added_to_pending',
        'plate': corrected_plate,
        'pending_count': len(profile['pending'])
    }

def get_vehicle_summary(plate):
    """Get a summary of a vehicle's patterns"""
    profiles = load_profiles()
    
    if plate not in profiles:
        return None
    
    profile = profiles[plate]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    summary = {
        'plate': plate,
        'total_readings': profile['total_readings'],
        'first_seen': profile['first_seen'],
        'last_seen': profile['last_seen'],
        'patterns': []
    }
    
    for i, bucket in enumerate(profile['buckets']):
        avg_hour = bucket['avg_minutes'] // 60
        avg_min = bucket['avg_minutes'] % 60
        days_str = ", ".join([day_names[d] for d in bucket['days_seen']])
        avg_conf = sum(bucket['confidence_scores']) / len(bucket['confidence_scores'])
        
        summary['patterns'].append({
            'pattern_id': i,
            'time': f"{avg_hour:02d}:{avg_min:02d}",
            'days': days_str,
            'sightings': bucket['count'],
            'avg_confidence': round(avg_conf, 3)
        })
    
    summary['pending_readings'] = len(profile['pending'])
    
    return summary
