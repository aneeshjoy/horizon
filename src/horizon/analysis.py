"""
Fast License Plate Pattern Analysis
Uses incremental bucket-based processing instead of re-reading the entire CSV.
Processing time: ~0.021 seconds per query (vs ~2 seconds with old approach)
"""

from .processor import get_vehicle_summary, load_profiles
import os

# --- SETTINGS ---
TARGET_PLATE = "242-WW-1023"  # Put a plate you want to test here
# ----------------

def calculate_routine_deviation_score(summary):
    """
    Calculate Routine Deviation Score (0-100%).
    
    How closely does the vehicle follow its own established patterns?
    - 95%+ = Follows routine exactly (Commuter)
    - 80-94% = Mostly follows routine (Regular commuter)
    - 60-79% = Some routine adherence (Occasional pattern)
    - 40-59% = Inconsistent routine (Erratic)
    - 0-39% = No routine (Suspicious)
    """
    if not summary or summary['total_readings'] < 5:
        return 0, "Insufficient data"
    
    patterns = summary['patterns']
    if not patterns:
        return 0, "No patterns identified"
    
    # Calculate pattern adherence: what % of sightings match identified patterns?
    total_sightings_in_patterns = sum(p['sightings'] for p in patterns)
    total_sightings = summary['total_readings']
    pattern_adherence = total_sightings_in_patterns / total_sightings if total_sightings > 0 else 0
    
    # Calculate confidence stability (consistency of detection confidence)
    confidences = [float(p['avg_confidence']) for p in patterns]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    # Confidence should be high and consistent (low variance)
    import statistics
    confidence_variance = statistics.stdev(confidences) if len(confidences) > 1 else 0
    confidence_stability = max(0, avg_confidence - confidence_variance)
    
    # Pattern concentration: are sightings concentrated in few patterns or spread?
    # Concentrated patterns = more routine; spread out = less routine
    pattern_weights = [p['sightings'] / total_sightings for p in patterns]
    
    # Calculate concentration (Herfindahl index): sum of squared pattern weights
    # High concentration (0.5+) means few strong patterns = routine
    # Low concentration (<0.2) means many weak patterns = erratic
    concentration = sum(w**2 for w in pattern_weights)
    
    # For commuters: concentration should be moderate-high (0.3-0.6 typical)
    # Pattern spread matters: if vehicle visits multiple times, it's more routine
    if concentration > 0.4:
        concentration_score = min(1.0, concentration / 0.4)  # Top out at 1.0
    else:
        concentration_score = concentration / 0.4  # Scale lower concentrations down
    
    # Combine factors into final score
    # Emphasis: pattern adherence (40%) + confidence (30%) + concentration (30%)
    routine_score = (
        pattern_adherence * 0.4 +
        confidence_stability * 0.3 +
        concentration_score * 0.3
    )
    
    # Round to percentage
    routine_deviation_score = round(routine_score * 100)
    
    reasoning = (
        f"Pattern adherence: {pattern_adherence:.1%} | "
        f"Avg confidence: {avg_confidence:.1%} | "
        f"Pattern concentration: {concentration:.2f}"
    )
    
    return routine_deviation_score, reasoning

def classify_vehicle(summary):
    """
    Classify a vehicle as Commuter, Unknown, or Suspicious.
    
    Uses Routine Deviation Score methodology:
    - 80-100%: COMMUTER - Follows established routine consistently
    - 60-79%: REGULAR - Some routine with minor variations
    - 40-59%: INCONSISTENT - Unpredictable visits
    - 0-39%: SUSPICIOUS - Highly erratic behavior
    """
    if not summary or summary['total_readings'] < 5:
        return "Unknown", "Insufficient sightings (< 5)", 0
    
    score, reasoning = calculate_routine_deviation_score(summary)
    
    if score >= 80:
        classification = "Commuter"
        detail = f"Routine deviation score {score}% - Highly predictable, follows established patterns"
    elif score >= 60:
        classification = "Commuter"
        detail = f"Routine deviation score {score}% - Regular patterns with some variation"
    elif score >= 40:
        classification = "Unknown"
        detail = f"Routine deviation score {score}% - Inconsistent behavior, insufficient pattern clarity"
    else:
        classification = "Suspicious"
        detail = f"Routine deviation score {score}% - Highly erratic, no consistent routine"
    
    return classification, detail, score

def analyze_plate_pattern(plate):
    """
    Analyze a vehicle's stored profile (runs in milliseconds).
    
    This uses pre-computed bucket profiles instead of re-processing
    the entire CSV file. Much faster!
    """
    profiles = load_profiles()
    
    if not profiles:
        print("No profiles found. Run init_profiles.py first to process the CSV data.")
        return
    
    # Find the plate (with fuzzy matching if needed)
    target_plate = plate
    if plate not in profiles:
        from difflib import SequenceMatcher
        best_match = None
        best_score = 0
        for stored_plate in profiles.keys():
            score = SequenceMatcher(None, plate, stored_plate).ratio()
            if score > best_score:
                best_score = score
                best_match = stored_plate
        
        if best_score < 0.85:
            print(f"Vehicle {plate} not found in profiles.")
            print(f"Available vehicles: {len(profiles)}")
            return
        
        target_plate = best_match
    
    summary = get_vehicle_summary(target_plate)
    
    if not summary:
        print(f"Vehicle {plate} not found in profiles.")
        return
    
    # Print results
    print(f"\n--- Pattern Analysis for {summary['plate']} ---")
    print(f"Total sightings: {summary['total_readings']}")
    print(f"First seen: {summary['first_seen']}")
    print(f"Last seen: {summary['last_seen']}")
    
    pattern_found = False
    
    if summary['patterns']:
        pattern_found = True
        print(f"\nIdentified {len(summary['patterns'])} Pattern(s):")
        for pattern in summary['patterns']:
            print(f"Pattern {pattern['pattern_id']}: {pattern['days']} around {pattern['time']} "
                  f"({pattern['sightings']} sightings, confidence: {pattern['avg_confidence']})")
    
    if summary['pending_readings'] > 0:
        print(f"\nPending readings: {summary['pending_readings']} "
              f"(will form new pattern when reaching 3 readings at similar times)")
    
    if not pattern_found:
        print(f"\nResult: No pattern identified yet (random or insufficient data)")
    
    # Classify the vehicle
    classification, detail, score = classify_vehicle(summary)
    print(f"\n{'='*60}")
    print(f"CLASSIFICATION: {classification}")
    print(f"Routine Deviation Score: {score}%")
    print(f"{'='*60}")
    print(f"Analysis: {detail}")
    print(f"{'='*60}\n")
    
    # Generate summary
    if summary['patterns']:
        num_patterns = len(summary['patterns'])
        days_active = len(set([day for pattern in summary['patterns'] 
                               for day in pattern['days'].split(', ')]))
        avg_confidence = sum(float(p['avg_confidence']) for p in summary['patterns']) / num_patterns
        
        print("SUMMARY:")
        print(f"  • Vehicle appears {times_label(num_patterns)} per day ({num_patterns} patterns)")
        print(f"  • Active on {days_active} days of the week")
        print(f"  • {summary['total_readings']} total sightings over {days_between(summary['first_seen'], summary['last_seen'])} days")
        print(f"  • Average confidence: {avg_confidence:.1%}")
        
        if classification == "Commuter":
            print(f"\n  ✓ Vehicle exhibits reliable commuting patterns")
            print(f"    Primary pattern: {summary['patterns'][0]['time']} on {summary['patterns'][0]['days']}")
            print(f"    Recommendation: Low priority - Expected vehicle")
        elif classification == "Suspicious":
            print(f"\n  ⚠ Vehicle shows irregular/suspicious behavior")
            print(f"    Recommendation: Monitor closely, compare with known theft patterns")
        else:
            print(f"\n  ? Vehicle data insufficient for clear classification")
            print(f"    Recommendation: Continue monitoring")

def times_label(num_patterns):
    """Convert number of patterns to human-readable label"""
    if num_patterns == 1:
        return "once"
    elif num_patterns <= 2:
        return "1-2 times"
    elif num_patterns <= 4:
        return "multiple times"
    else:
        return f"{num_patterns} times"

def days_between(start_str, end_str):
    """Calculate days between two ISO timestamps"""
    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        delta = abs((end - start).days)
        return max(1, delta)
    except:
        return "unknown"

# Run the analysis
if __name__ == "__main__":
    analyze_plate_pattern(TARGET_PLATE)