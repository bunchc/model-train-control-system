CREATE TABLE trains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    speed INTEGER NOT NULL,
    position INTEGER NOT NULL,
    voltage FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trains_status ON trains(status);
CREATE INDEX idx_trains_position ON trains(position);

SELECT create_hypertable('trains', 'created_at');