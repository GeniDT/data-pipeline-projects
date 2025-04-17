USE inventory_system;

CREATE TABLE replenishment_alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    units_needed INT NOT NULL,
    processed BOOLEAN DEFAULT FALSE
);