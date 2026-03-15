"""
Configuration management service
"""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

from src.webui.models.config import (
    SystemConfig,
    ConfigValidationResult,
    ReprocessStatus,
)


class ConfigService:
    """Manage system configuration loading, saving, and validation"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file or "config/settings.json")
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Create config file if it doesn't exist"""
        if not self.config_file.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            default_config = self._get_default_config()
            self._save_config(default_config)

    def load_config(self) -> SystemConfig:
        """Load current configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)

            # Add import_config if missing (backward compatibility)
            if 'import_config' not in data:
                data['import_config'] = {
                    'auto_import_on_startup': False,
                    'auto_rebuild_after_import': True,
                    'import_db_path': 'data/external/frigate.db',
                    'import_after_date': None
                }
            # Add auto_rebuild_after_import if missing (backward compatibility)
            elif 'auto_rebuild_after_import' not in data['import_config']:
                data['import_config']['auto_rebuild_after_import'] = True

            return SystemConfig(**data)
        except Exception as e:
            # If loading fails, return default config
            return self._get_default_config()

    def save_config(self, config: SystemConfig) -> SystemConfig:
        """Save configuration to file"""
        config_dict = config.dict()
        config_dict['last_modified'] = datetime.now().isoformat()

        with open(self.config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)

        return config

    def validate_config(self, config: SystemConfig) -> ConfigValidationResult:
        """
        Validate configuration for correctness and consistency
        """
        errors = []
        warnings = []

        # Check classification thresholds
        if config.classification.commuter_threshold <= config.classification.unknown_threshold:
            errors.append("Commuter threshold must be greater than Unknown threshold")

        # Check RDS weights sum to approximately 1.0
        weights = [
            config.classification.pattern_adherence_weight,
            config.classification.confidence_stability_weight,
            config.classification.pattern_concentration_weight
        ]
        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(f"RDS weights must sum to 1.0, currently {weight_sum:.2f}")

        # Warnings for non-standard values
        if config.pattern_detection.bucket_tolerance_minutes > 90:
            warnings.append("High bucket tolerance may create overly broad patterns")

        if config.pattern_detection.bucket_tolerance_minutes < 30:
            warnings.append("Low bucket tolerance may fragment patterns")

        if config.pattern_detection.confidence_threshold > 0.8:
            warnings.append("High confidence threshold may filter many valid readings")

        if config.display.auto_refresh_interval_seconds > 0 and config.display.auto_refresh_interval_seconds < 30:
            warnings.append("Fast auto-refresh may impact performance")

        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def reset_to_defaults(self) -> SystemConfig:
        """Reset configuration to default values"""
        default_config = self._get_default_config()
        return self.save_config(default_config)

    def _get_default_config(self) -> SystemConfig:
        """Get default configuration"""
        return SystemConfig()


# Singleton instances
_config_service = None


def get_config_service() -> ConfigService:
    """Get singleton config service instance"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
