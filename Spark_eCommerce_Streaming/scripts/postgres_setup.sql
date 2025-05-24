CREATE TABLE user_events (
    event_id INTEGER NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    product_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP,
    PRIMARY KEY (event_id)
);