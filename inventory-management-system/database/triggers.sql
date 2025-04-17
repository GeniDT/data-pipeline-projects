-- Order Placement and Inventory Management 
-- Trigger implements: Multi-product order processing, real-time stock deduction, and inventory change tracking

DELIMITER //
CREATE TRIGGER track_inventory_changes
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    DECLARE v_stock_change INT;
    DECLARE v_change_type VARCHAR(20);
    DECLARE v_reference_id INT DEFAULT NULL;

    -- Calculate absolute stock difference
    SET v_stock_change = ABS(NEW.stock_quantity - OLD.stock_quantity);

    -- Only log if there's an actual change
    IF v_stock_change > 0 THEN
        -- Determine change direction
        SET v_change_type = IF(NEW.stock_quantity > OLD.stock_quantity, 'replenishment', 'order');
        
        -- Get latest order reference (only for deductions)
        IF v_change_type = 'order' THEN
            SET v_reference_id = (
                SELECT od.order_id 
                FROM order_details od
                WHERE od.product_id = NEW.product_id
                ORDER BY od.order_id DESC
                LIMIT 1
            );
        END IF;
        
        -- Insert only what your table supports
        INSERT INTO inventory_logs (
            product_id, 
            change_date, 
            change_type, 
            quantity_changed,
            reference_id
        ) VALUES (
            NEW.product_id, 
            NOW(), 
            v_change_type, 
            v_stock_change,
            v_reference_id
        );
    END IF;
END //
DELIMITER ;