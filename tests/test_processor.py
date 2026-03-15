"""
Unit tests for the processor module
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from horizon.processor import (
    process_reading,
    load_profiles,
    save_profiles,
    get_vehicle_summary,
    similarity_score,
    correct_ocr_error,
    minutes_from_midnight,
    fits_bucket,
)


@pytest.fixture
def mock_profiles_file():
    """Mock the PROFILES_FILE constant for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({}, f)
        temp_path = f.name

    with patch('horizon.processor.PROFILES_FILE', temp_path):
        yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestSimilarityScore:
    """Tests for string similarity scoring"""

    def test_identical_strings(self):
        assert similarity_score("ABC-123", "ABC-123") == 1.0

    def test_similar_strings(self):
        score = similarity_score("ABC-123", "ABc-123")
        assert score > 0.8

    def test_different_strings(self):
        score = similarity_score("ABC-123", "XYZ-789")
        assert score < 0.5

    def test_clean_plate_string(self):
        from horizon.processor import clean_plate_string
        assert clean_plate_string("AB?C-123") == "ABC-123"
        assert clean_plate_string(" ABC-123 ") == "ABC-123"


class TestOCRCorrection:
    """Tests for OCR error correction"""

    def test_no_correction_needed(self):
        known = ["ABC-123", "DEF-456"]
        result = correct_ocr_error("ABC-123", known)
        assert result == "ABC-123"

    def test_correction_with_similar(self):
        known = ["ABC-123", "DEF-456"]
        result = correct_ocr_error("ABc-123", known)
        assert result == "ABC-123"  # Should correct to known

    def test_no_similar_match(self):
        known = ["ABC-123", "DEF-456"]
        result = correct_ocr_error("XYZ-789", known)
        assert result == "XYZ-789"  # Should return original

    def test_question_mark_placeholder(self):
        known = ["ABC-123", "DEF-456"]
        result = correct_ocr_error("AB?-123", known)
        assert result == "AB?-123"  # Should not try to match


class TestTimeFunctions:
    """Tests for time-related functions"""

    def test_minutes_from_midnight(self):
        assert minutes_from_midnight("00:00:00") == 0
        assert minutes_from_midnight("01:00:00") == 60
        assert minutes_from_midnight("12:30:00") == 750
        assert minutes_from_midnight("23:59:59") == 1439

    def test_fits_bucket(self):
        bucket = {'avg_minutes': 480}  # 08:00

        # Exactly at bucket time
        assert fits_bucket(480, bucket, tolerance=45) == True

        # Within tolerance
        assert fits_bucket(440, bucket, tolerance=45) == True
        assert fits_bucket(520, bucket, tolerance=45) == True

        # At tolerance boundary (inclusive)
        assert fits_bucket(435, bucket, tolerance=45) == True  # 480 - 435 = 45
        assert fits_bucket(525, bucket, tolerance=45) == True  # 525 - 480 = 45

        # Just outside tolerance
        assert fits_bucket(434, bucket, tolerance=45) == False  # 480 - 434 = 46
        assert fits_bucket(526, bucket, tolerance=45) == False  # 526 - 480 = 46


class TestProfileManagement:
    """Tests for profile loading and saving"""

    def test_load_empty_profiles(self, mock_profiles_file):
        profiles = load_profiles()
        assert profiles == {}

    def test_save_and_load_profiles(self, mock_profiles_file):
        test_profiles = {
            "ABC-123": {
                "buckets": [],
                "pending": [],
                "first_seen": "2026-03-09T12:00:00",
                "last_seen": "2026-03-09T12:00:00",
                "total_readings": 0
            }
        }
        save_profiles(test_profiles)
        loaded = load_profiles()
        assert loaded == test_profiles


class TestProcessReading:
    """Tests for processing individual readings"""

    def test_low_confidence_filtered(self, mock_profiles_file):
        profiles, result = process_reading(
            plate="ABC-123",
            date_str="2026-03-09",
            time_str="12:00:00",
            confidence=0.5  # Below 0.65 threshold
        )
        assert result['status'] == 'filtered'

    def test_high_confidence_processed(self, mock_profiles_file):
        profiles, result = process_reading(
            plate="ABC-123",
            date_str="2026-03-09",
            time_str="12:00:00",
            confidence=0.8
        )
        assert result['status'] in ['added_to_pending', 'added_to_bucket', 'created_new_bucket']

    def test_first_reading_creates_pending(self, mock_profiles_file):
        profiles, result = process_reading(
            plate="ABC-123",
            date_str="2026-03-09",
            time_str="12:00:00",
            confidence=0.8
        )
        assert result['status'] == 'added_to_pending'
        assert 'ABC-123' in profiles

    def test_three_similar_readings_create_bucket(self, mock_profiles_file):
        plate = "ABC-123"
        time = "12:00:00"

        # First reading
        process_reading(plate, "2026-03-09", time, 0.8)
        # Second reading (same time)
        process_reading(plate, "2026-03-10", time, 0.8)
        # Third reading (same time - should create bucket)
        profiles, result = process_reading(plate, "2026-03-11", time, 0.8)

        assert result['status'] == 'created_new_bucket'
        assert len(profiles[plate]['buckets']) == 1


class TestVehicleSummary:
    """Tests for vehicle summary generation"""

    def test_unknown_vehicle(self, mock_profiles_file):
        summary = get_vehicle_summary("UNKNOWN-123")
        assert summary is None

    def test_vehicle_summary_structure(self, mock_profiles_file):
        # Create a vehicle with some data
        profiles = {
            "ABC-123": {
                "buckets": [
                    {
                        "avg_minutes": 480,
                        "days_seen": [0, 1, 2, 3, 4],
                        "confidence_scores": [0.9, 0.85, 0.95],
                        "count": 3
                    }
                ],
                "pending": [],
                "first_seen": "2026-03-09T08:00:00",
                "last_seen": "2026-03-13T08:00:00",
                "total_readings": 3
            }
        }
        save_profiles(profiles)

        summary = get_vehicle_summary("ABC-123")
        assert summary is not None
        assert summary['plate'] == "ABC-123"
        assert summary['total_readings'] == 3
        assert len(summary['patterns']) == 1
        assert summary['patterns'][0]['time'] == "08:00"
        assert summary['patterns'][0]['days'] == "Mon, Tue, Wed, Thu, Fri"
