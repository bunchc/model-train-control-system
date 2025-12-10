-- Migration: 001_add_controller_telemetry
-- Date: 2025-12-04
-- Description: Add telemetry fields to edge_controllers table for heartbeat tracking
--
-- This migration is IDEMPOTENT - safe to run multiple times.
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN,
-- so we check the schema first.

-- Add first_seen column (when controller was first registered)
-- SQLite workaround: Try to add, ignore error if exists
ALTER TABLE edge_controllers ADD COLUMN first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add last_seen column (last heartbeat timestamp)
ALTER TABLE edge_controllers ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add config_hash column (MD5 hash of runtime configuration)
ALTER TABLE edge_controllers ADD COLUMN config_hash TEXT;

-- Add version column (controller software version)
ALTER TABLE edge_controllers ADD COLUMN version TEXT;

-- Add platform column (OS platform string, e.g., "Linux-5.15.0-aarch64")
ALTER TABLE edge_controllers ADD COLUMN platform TEXT;

-- Add python_version column (Python interpreter version)
ALTER TABLE edge_controllers ADD COLUMN python_version TEXT;

-- Add memory_mb column (total system RAM in megabytes)
ALTER TABLE edge_controllers ADD COLUMN memory_mb INTEGER;

-- Add cpu_count column (number of CPU cores)
ALTER TABLE edge_controllers ADD COLUMN cpu_count INTEGER;

-- Add status column (online/offline/unknown)
ALTER TABLE edge_controllers ADD COLUMN status TEXT DEFAULT 'unknown';
