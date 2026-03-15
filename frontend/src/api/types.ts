// Vehicle types
export interface SightingPattern {
  pattern_id: number
  time: string
  days: string[]
  sightings: number
  avg_confidence: number
  time_minutes: number
}

export interface VehicleSummary {
  plate: string
  total_readings: number
  first_seen: string
  last_seen: string
  patterns: SightingPattern[]
  pending_readings: number
  classification: 'Commuter' | 'Unknown' | 'Suspicious'
  routine_deviation_score: number
  confidence_score: number
}

export interface VehicleListItem {
  plate: string
  total_readings: number
  classification: string
  last_seen: string
  pattern_count: number
}

// Grid types
export interface GridCell {
  day: number
  time_slot: number
  count: number
  avg_confidence: number
  pattern_ids: number[]
}

export interface GridRow {
  time_slot: number
  time_label: string
  cells: GridCell[]
}

export interface PatternGrid {
  vehicle_plate: string
  rows: GridRow[]
  max_count: number
  total_patterns: number
}

// MQTT types
export interface MQTTConfig {
  enabled: boolean
  broker_host: string
  broker_port: number
  username: string | null
  password: string | null
  client_id: string
  topic_prefix: string
  qos: number
  retry_interval: number
  max_retries: number
  connection_timeout: number
  timezone: string
  enabled_cameras: string[]
  enabled_cameras_mode: 'whitelist' | 'blacklist'
}

export interface MQTTStatus {
  enabled: boolean
  connected: boolean
  running: boolean
  broker_host: string
  broker_port: number
  client_id: string
  uptime_seconds: number | null
  messages_received: number
  messages_processed: number
  messages_ignored: number
  last_message_at: string | null
  error_message: string | null
  detected_cameras: string[]
  stats: {
    processor: {
      processed: number
      duplicates: number
      filtered: number
      errors: number
    }
    deduplicator: {
      size: number
      max_size: number
      hits: number
      misses: number
      evictions: number
      hit_rate: string
    }
    profiles: {
      total_profiles: number
      pending_updates: number
      total_updates: number
      total_saves: number
      last_save: string | null
    }
  }
}

// Configuration types
export interface PatternDetectionConfig {
  bucket_tolerance_minutes: number
  min_pattern_samples: number
  confidence_threshold: number
  ocr_similarity_threshold: number
}

export interface ClassificationConfig {
  commuter_threshold: number
  unknown_threshold: number
  pattern_adherence_weight: number
  confidence_stability_weight: number
  pattern_concentration_weight: number
}

export interface DisplayConfig {
  grid_time_granularity_minutes: number
  auto_refresh_interval_seconds: number
}

export interface SystemConfig {
  mqtt: MQTTConfig
  pattern_detection: PatternDetectionConfig
  classification: ClassificationConfig
  display: DisplayConfig
  import_config: ImportConfig
}

export interface ConfigValidationResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
}

export interface ReprocessStatus {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'none'
  progress: number
  total_vehicles: number
  processed_vehicles: number
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

// Import types
export interface ImportConfig {
  auto_import_on_startup: boolean
  auto_rebuild_after_import: boolean
  import_db_path: string
  import_after_date: string | null
}

export interface ImportStatus {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'none'
  progress: number
  total_events: number
  processed_events: number
  filtered_events: number
  plates_created: number
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  db_path: string
  db_size_mb: number
  rebuild_triggered: boolean
}

export const DEFAULT_REPROCESS_STATUS: ReprocessStatus = {
  job_id: '',
  status: 'none',
  progress: 0,
  total_vehicles: 0,
  processed_vehicles: 0,
  started_at: null,
  completed_at: null,
  error_message: null,
}

// Trend types
export interface TrendData {
  plate: string
  weeks_analyzed: number
  weekly_data: Array<{
    week_start: string
    sightings: number
    avg_confidence: number
  }>
  trend: {
    direction: string
    percent_change: number
  }
}
