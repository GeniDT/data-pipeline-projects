USE inventory_system;

-- Inventory logs table
CREATE TABLE inventory_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantity_change INT NOT NULL,
    change_type VARCHAR(20),
    reference_id INT,
    order_id INT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);