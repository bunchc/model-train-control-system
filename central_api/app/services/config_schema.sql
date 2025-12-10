-- Table for train status (new for status updates)
CREATE TABLE IF NOT EXISTS train_status (
    train_id TEXT PRIMARY KEY,
    speed INTEGER,
    voltage REAL,
    current REAL,
    position TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Table for plugins
CREATE TABLE IF NOT EXISTS plugins (
    name TEXT PRIMARY KEY,
    description TEXT,
    config TEXT -- JSON string
);

-- Table for edge controllers
CREATE TABLE IF NOT EXISTS edge_controllers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    address TEXT,
    enabled BOOLEAN NOT NULL,
    -- Telemetry fields (added 2025-12-04)
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config_hash TEXT,
    version TEXT,
    platform TEXT,
    python_version TEXT,
    memory_mb INTEGER,
    cpu_count INTEGER,
    status TEXT DEFAULT 'unknown'
);

-- Table for trains (referenced by edge_controller)
CREATE TABLE IF NOT EXISTS trains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    model TEXT,
    plugin_name TEXT NOT NULL,
    plugin_config TEXT,
    edge_controller_id TEXT NOT NULL,
    invert_directions BOOLEAN DEFAULT 0,
    FOREIGN KEY(edge_controller_id) REFERENCES edge_controllers(id)
);

-- Table for config metadata
CREATE TABLE IF NOT EXISTS config_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
