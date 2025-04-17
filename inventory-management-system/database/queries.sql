USE inventory_system;

-- Phase 2
-- Order Placement and Inventory Management
-- Test Order Placement Logic
-- Should FAIL with clear error (assuming only 50 wireless mouse in stock)
CALL place_order(1002, '1,2', '60');

-- Should SUCCEED (if enough stock)
CALL place_order(1001, '1,2', '20');

-- Should handle multiple products in a single order
CALL place_order(1002, '1,2', '3,4');


-- Phase 3
-- Monitoring and Reporting
-- Simulate a stock replenishment
UPDATE products 
SET stock_quantity = stock_quantity + 10 
WHERE product_id = 101;

-- Verify Inventory Log Update
SELECT * 
FROM inventory_logs 
WHERE product_id = 101 
ORDER BY change_date DESC 
LIMIT 1;


-- Retrieve Customer Order History
SELECT * 
FROM customer_orders_with_items
WHERE customer_id = 1005
ORDER BY order_date DESC;

-- Report on Low Stock Products
SELECT * 
FROM low_stock_report;


-- Trigger Replenishment for Critical Stock
CALL generate_urgent_replenishment(10);

-- Categorize Customers by Spending
CALL categorize_customers();
SELECT * 
FROM customer_tier_report;

-- Test Bulk Discount Order Logic
CALL place_order_with_discounts(
    1001, 
    CURDATE(), 
    '[{"product_id": 101, "quantity": 15}, {"product_id": 102, "quantity": 2}]'
);


-- Phase 4
-- Prepare for Stock Replenishment
-- Set stock below reorder level for testing
UPDATE products
SET stock_quantity = 4
WHERE product_id = 101;


-- Check Products Needing Reorder
SELECT product_id, 
		name, 
        stock_quantity, 
        reorder_level
FROM products
WHERE stock_quantity < reorder_level;

-- Test Automated Order Processing
CALL process_order_automation(101, '[{"product_id":1,"quantity":5},{"product_id":2,"quantity":12}]');

-- Verify Inventory and Replenishment Logs
SELECT * 
FROM inventory_logs;
SELECT * 
FROM replenishment_alerts;
SELECT * 
FROM customers WHERE customer_id = 1001;



-- Phase 5
-- Advanced Queries and Optimizations 
-- Summarize Orders
SELECT * FROM order_summary;


-- Summarize stock
SELECT * FROM stock_summary;