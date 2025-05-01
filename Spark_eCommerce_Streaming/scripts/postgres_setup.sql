CREATE TABLE IF NOT EXISTS events (
    timestamp TIMESTAMP,
    user_id VARCHAR(36),
    product_id VARCHAR(50),
    event_type VARCHAR(20),
    PRIMARY KEY (timestamp, user_id, product_id)
);