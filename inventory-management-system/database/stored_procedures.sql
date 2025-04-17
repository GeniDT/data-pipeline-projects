USE inventory_system;

-- Order Placement and Inventory Management 
-- PROCEDURE: place_order, processes multi-product orders with stock validation, Handle multiple products in a single order
-- Handle customer orders 
DELIMITER //

CREATE PROCEDURE place_order(
    IN p_customer_id INT,
    IN p_product_ids VARCHAR(255),
    IN p_quantities VARCHAR(255)
)
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_total DECIMAL(12,2) DEFAULT 0;
    DECLARE i INT DEFAULT 1;
    DECLARE v_product_id INT;
    DECLARE v_quantity INT;
    DECLARE v_unit_price DECIMAL(10,2);
    DECLARE v_current_stock INT;
    DECLARE v_items_count INT;
    DECLARE v_error_message VARCHAR(255);
    
    SET v_items_count = LENGTH(p_product_ids) - LENGTH(REPLACE(p_product_ids, ',', '')) + 1;
    
    START TRANSACTION;
    
    INSERT INTO orders (customer_id, order_date, total_amount)
    VALUES (p_customer_id, NOW(), 0);
    SET v_order_id = LAST_INSERT_ID();
    
    WHILE i <= v_items_count DO
        SET v_product_id = SUBSTRING_INDEX(SUBSTRING_INDEX(p_product_ids, ',', i), ',', -1);
        SET v_quantity = SUBSTRING_INDEX(SUBSTRING_INDEX(p_quantities, ',', i), ',', -1);
        
        SELECT price, stock_quantity INTO v_unit_price, v_current_stock 
        FROM products 
        WHERE product_id = v_product_id
        FOR UPDATE;
        
        IF v_current_stock < v_quantity THEN
            SET v_error_message = CONCAT('Insufficient stock for Product ID ', v_product_id, 
                                       '. Available: ', v_current_stock, ', Requested: ', v_quantity);
            ROLLBACK;
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_error_message;
        END IF;
        
        INSERT INTO order_details (
            order_id, 
            product_id, 
            quantity, 
            unit_price, 
            discount
        )
        VALUES (
            v_order_id, 
            v_product_id, 
            v_quantity, 
            v_unit_price, 
            0  -- No discount
        );
        
        SET v_total = v_total + (v_unit_price * v_quantity);
        
        UPDATE products 
        SET stock_quantity = stock_quantity - v_quantity 
        WHERE product_id = v_product_id;
        
        SET i = i + 1;
    END WHILE;
    
    UPDATE orders 
    SET total_amount = v_total 
    WHERE order_id = v_order_id;
    
    COMMIT;
    
    SELECT CONCAT(
        'Order #', v_order_id, 
        ' successfully placed. ', 
        'Items: ', v_items_count, 
        ', Total: $', ROUND(v_total, 2)
    ) AS order_confirmation;
END //

DELIMITER ;


-- Handle all inventory changes (orders, replenishments)
DELIMITER //
CREATE PROCEDURE update_product_stock(
    IN p_product_id INT,              
    IN p_quantity_changed INT,         
    IN p_change_type VARCHAR(20)
)
BEGIN
    DECLARE v_old_quantity INT;
    
    START TRANSACTION;
    
    -- Get current quantity with lock (prevents concurrent modifications)
    SELECT stock_quantity INTO v_old_quantity 
    FROM products 
    WHERE product_id = p_product_id
    FOR UPDATE;
    
    -- Update product stock
    UPDATE products
    SET stock_quantity = stock_quantity + p_quantity_changed
    WHERE product_id = p_product_id;
    
    -- Log the change to inventory_log (audit trail)
    INSERT INTO inventory_logs (
		log_id,
        product_id,
        change_type,
        old_quantity,
        new_quantity,
        order_id
    )
    VALUES (
        p_product_id,
        v_old_quantity,                      
        v_old_quantity + p_quantity_changed,  
        p_change_type
    );
    
    COMMIT;
END//
DELIMITER ;


-- Flag any product that has stock level below its reorder points
DELIMITER //
CREATE PROCEDURE generate_urgent_replenishment(IN min_units_needed INT)
BEGIN
    SELECT 
        product_id,
        name,
        stock_quantity,
        reorder_level,
        units_needed,
        CONCAT('Order ', units_needed, ' units') AS action
    FROM low_stock_report
    WHERE units_needed >= min_units_needed;
END //
DELIMITER ;


-- Customer insights based on customer spending habits
DELIMITER //
CREATE PROCEDURE categorize_customers()
BEGIN
    -- Update tiers in a single query (Gold ≥1000, Bronze ≥500, Silver ≥100)
    UPDATE customers c
    LEFT JOIN (
        SELECT 
            customer_id,
            SUM(total_amount) AS total_spent
        FROM orders
        GROUP BY customer_id
    ) o ON c.customer_id = o.customer_id
    SET c.tier = CASE
        WHEN o.total_spent >= 1000 THEN 'Gold'
        WHEN o.total_spent >= 500 THEN 'Bronze'
        WHEN o.total_spent >= 100 THEN 'Silver'
        ELSE 'New' -- For customers with <$100 spending
    END;
END //
DELIMITER ;


-- Allow for bulk discounts
DELIMITER //
CREATE PROCEDURE place_order_with_discounts(
    IN p_customer_id INT,
    IN p_order_date DATE,
    IN p_items JSON
)
BEGIN
    DECLARE v_order_id INT;
    DECLARE i INT DEFAULT 0;
    DECLARE v_items_count INT;
    DECLARE v_product_id INT;
    DECLARE v_quantity INT;
    DECLARE v_unit_price DECIMAL(10,2);
    DECLARE v_discount DECIMAL(10,2);
    DECLARE v_final_price DECIMAL(10,2);
    DECLARE v_current_stock INT;
    DECLARE v_total_order_amount DECIMAL(12,2) DEFAULT 0;
    DECLARE v_total_items INT DEFAULT 0;
    DECLARE v_order_discount DECIMAL(5,2) DEFAULT 0;
    DECLARE v_error_msg TEXT;

    -- Start transaction
    START TRANSACTION;

    -- Calculate total items for order-level discount
    SET v_items_count = JSON_LENGTH(p_items);
    WHILE i < v_items_count DO
        SET v_quantity = CAST(JSON_UNQUOTE(JSON_EXTRACT(p_items, CONCAT('$[', i, '].quantity'))) AS UNSIGNED);
        SET v_total_items = v_total_items + v_quantity;
        SET i = i + 1;
    END WHILE;
    
    -- Reset counter for main processing
    SET i = 0;

    -- Determine order-level bulk discount (tiered)
    IF v_total_items >= 50 THEN
        SET v_order_discount = 15.0;
    ELSEIF v_total_items >= 25 THEN
        SET v_order_discount = 10.0;
    ELSEIF v_total_items >= 10 THEN
        SET v_order_discount = 5.0;
    END IF;

    -- Insert new order
    INSERT INTO orders (customer_id, order_date, discount)
    VALUES (p_customer_id, p_order_date, v_order_discount);

    SET v_order_id = LAST_INSERT_ID();

    -- Process each order item
    WHILE i < v_items_count DO
        SET v_product_id = CAST(JSON_UNQUOTE(JSON_EXTRACT(p_items, CONCAT('$[', i, '].product_id'))) AS UNSIGNED);
        SET v_quantity = CAST(JSON_UNQUOTE(JSON_EXTRACT(p_items, CONCAT('$[', i, '].quantity'))) AS UNSIGNED);

        -- Fetch unit price and validate stock
        SELECT price, stock_quantity INTO v_unit_price, v_current_stock 
        FROM products 
        WHERE product_id = v_product_id
        FOR UPDATE;

        IF v_current_stock < v_quantity THEN
            SET v_error_msg = CONCAT('Insufficient stock for product ID ', 
                                   v_product_id, 
                                   '. Available: ', 
                                   v_current_stock, 
                                   ', Requested: ', 
                                   v_quantity);
            ROLLBACK;
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_error_msg;
        END IF;

        -- Calculate item-level discount
        SET v_discount = CASE 
            WHEN v_quantity >= 10 THEN v_unit_price * 0.05
            ELSE 0 
        END;
        
        -- Apply discounts
        SET v_final_price = (v_unit_price - v_discount) * v_quantity * (1 - v_order_discount/100);

        -- Insert into order_items
        INSERT INTO order_items (
            order_id, product_id, quantity, unit_price, discount, final_price
        )
        VALUES (
            v_order_id, v_product_id, v_quantity, v_unit_price, 
            (v_discount/v_unit_price)*100,
            v_final_price
        );

        -- Update stock
        UPDATE products
        SET stock_quantity = stock_quantity - v_quantity
        WHERE product_id = v_product_id;

        SET v_total_order_amount = v_total_order_amount + v_final_price;
        SET i = i + 1;
    END WHILE;

    -- Finalize order
    UPDATE orders
    SET total_amount = v_total_order_amount
    WHERE order_id = v_order_id;

    COMMIT;

    -- Return success (using direct SELECT without CONCAT)
    SELECT 
        'Order placed successfully' AS message,
        v_order_id AS order_id,
        v_order_discount AS discount_percent,
        v_total_order_amount AS total_amount;
END //

DELIMITER ;


-- Implement stock replenishment
DELIMITER //
CREATE PROCEDURE replenish_stock()
BEGIN
    DECLARE v_product_id INT;
    DECLARE v_reorder_level INT;
    DECLARE v_current_stock INT;
    DECLARE v_new_stock INT;
    
    -- Cursor to loop through products with low stock
    DECLARE cur CURSOR FOR
    SELECT product_id, reorder_level, stock_quantity
    FROM products
    WHERE stock_quantity <= reorder_level;
    
    OPEN cur;
    
    -- Loop through the products that need replenishment
    read_loop: LOOP
        FETCH cur INTO v_product_id, v_reorder_level, v_current_stock;
        
        -- Exit loop when no more rows to process
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Calculate the new stock (reorder level - current stock)
        SET v_new_stock = v_reorder_level - v_current_stock;
        
        -- Update the stock quantity
        UPDATE products
        SET stock_quantity = stock_quantity + v_new_stock
        WHERE product_id = v_product_id;
        
        -- Log the replenishment action in the inventory log
        INSERT INTO inventory_logs (
            product_id,
            change_date,
            change_type,
            quantity_changed
        ) VALUES (
            v_product_id,
            NOW(),
            'replenishment',
            v_new_stock
        );
    END LOOP;
    
    CLOSE cur;
END //
DELIMITER ;



-- Automate solution for inventory system management
DELIMITER //
CREATE TRIGGER after_order_insert
AFTER INSERT ON order_details
FOR EACH ROW
BEGIN
    -- Automatically deduct stock
    UPDATE products 
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
    
    -- Log inventory change
    INSERT INTO inventory_logs (
        product_id, 
        change_type, 
        quantity_changed, 
        reference_id
    )
    VALUES (
        NEW.product_id,
        'order',
        -NEW.quantity,
        NEW.order_id
    );
END //
DELIMITER ;


-- Automate replenishment alert
DELIMITER //
CREATE EVENT check_low_stock
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    INSERT INTO replenishment_alerts (product_id, units_needed)
    SELECT 
        product_id, 
        reorder_level - stock_quantity
    FROM products
    WHERE stock_quantity < reorder_level;
END //
DELIMITER ;

-- Automate order totals
DELIMITER //
CREATE TRIGGER update_order_total
AFTER INSERT ON order_details
FOR EACH ROW
BEGIN
    UPDATE orders o
    SET total_amount = (
        SELECT SUM(unit_price * quantity * (1 - discount/100))
        FROM order_details
        WHERE order_id = NEW.order_id
    )
    WHERE order_id = NEW.order_id;
END //
DELIMITER ;


-- Schedule categorization
DELIMITER //
CREATE EVENT update_customer_tiers
ON SCHEDULE EVERY 1 WEEK
DO
BEGIN
    UPDATE customers c
    SET tier = (
        SELECT CASE
            WHEN SUM(total_amount) >= 1000 THEN 'Gold'
            WHEN SUM(total_amount) >= 500 THEN 'Silver'
            ELSE 'Bronze'
        END
        FROM orders
        WHERE customer_id = c.customer_id
    );
END //
DELIMITER ;


-- Combined automation procedure
DELIMITER //
CREATE PROCEDURE process_order_automation(
    IN p_customer_id INT,
    IN p_items JSON
)
BEGIN
    DECLARE v_order_id INT;
    
    -- Create order header
    INSERT INTO orders (customer_id, order_date) 
    VALUES (p_customer_id, CURDATE());
    
    SET v_order_id = LAST_INSERT_ID();
    
    -- Process items (triggers will handle stock/totals)
    SET @i = 0;
    SET @item_count = JSON_LENGTH(p_items);
    
    WHILE @i < @item_count DO
        INSERT INTO order_details (
            order_id,
            product_id,
            quantity,
            unit_price,
            discount
        )
        SELECT 
            v_order_id,
            JSON_EXTRACT(p_items, CONCAT('$[', @i, '].product_id')),
            JSON_EXTRACT(p_items, CONCAT('$[', @i, '].quantity')),
            p.price,
            CASE 
                WHEN JSON_EXTRACT(p_items, CONCAT('$[', @i, '].quantity')) >= 10 THEN 5 
                ELSE 0 
            END
        FROM products p
        WHERE p.product_id = JSON_EXTRACT(p_items, CONCAT('$[', @i, '].product_id'));
        
        SET @i = @i + 1;
    END WHILE;
    
    -- Auto-categorize customer
    CALL update_customer_tier(p_customer_id);
    
    -- Return success
    SELECT CONCAT('Order ', v_order_id, ' processed automatically') AS result;
END //
DELIMITER ;

-- Enable event scheduler
SET GLOBAL event_scheduler = ON;