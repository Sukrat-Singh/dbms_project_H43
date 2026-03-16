-- triggers/triggers.sql
-- Run this after schema.sql has been executed.

DELIMITER $$

-- 1) Calculate time_taken_minutes before inserting Turnaround
DROP TRIGGER IF EXISTS trg_calc_turnaround$$
CREATE TRIGGER trg_calc_turnaround
BEFORE INSERT ON Turnaround
FOR EACH ROW
BEGIN
    IF NEW.report_time IS NULL OR NEW.collection_time IS NULL THEN
        SET NEW.time_taken_minutes = NULL;
    ELSE
        SET NEW.time_taken_minutes = TIMESTAMPDIFF(MINUTE, NEW.collection_time, NEW.report_time);
    END IF;
END$$

-- 2) Validate LabResult: prevent null result_value for tests marked numeric (optional check)
DROP TRIGGER IF EXISTS trg_validate_result$$
CREATE TRIGGER trg_validate_result
BEFORE INSERT ON LabResult
FOR EACH ROW
BEGIN
    DECLARE v_is_numeric BOOLEAN DEFAULT FALSE;
    SELECT is_numeric INTO v_is_numeric
      FROM LabTest t
      JOIN OrderTest ot ON ot.test_id = t.test_id
      WHERE ot.order_test_id = NEW.order_test_id
      LIMIT 1;
    IF v_is_numeric = TRUE AND (NEW.result_value IS NULL OR NEW.result_value = '') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Numeric test must have a non-null result_value';
    END IF;
END$$

-- 3) After a result is reported: update OrderTest.result_status and possibly LabOrder.status; create Alerts for critical flags
DROP TRIGGER IF EXISTS trg_after_result$$
CREATE TRIGGER trg_after_result
AFTER INSERT ON LabResult
FOR EACH ROW
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_pending_count INT;
    -- mark order_test as Reported
    UPDATE OrderTest
      SET result_status = 'Reported'
      WHERE order_test_id = NEW.order_test_id;

    -- get parent order_id
    SELECT order_id INTO v_order_id FROM OrderTest WHERE order_test_id = NEW.order_test_id LIMIT 1;

    -- if there are any pending order_tests for this order, count them
    SELECT COUNT(*) INTO v_pending_count
      FROM OrderTest ot
      LEFT JOIN LabResult lr ON ot.order_test_id = lr.order_test_id
      WHERE ot.order_id = v_order_id AND ot.result_status <> 'Reported';

    -- if none pending => set LabOrder.status = 'Completed'
    IF v_pending_count = 0 THEN
        UPDATE LabOrder SET status = 'Completed' WHERE order_id = v_order_id;
    ELSE
        UPDATE LabOrder SET status = 'In Progress' WHERE order_id = v_order_id;
    END IF;

    -- create an alert for 'Critical' flagged results
    IF NEW.flag = 'Critical' THEN
        INSERT INTO Alerts(order_test_id, alert_type, message)
        VALUES (NEW.order_test_id, 'Critical Result', CONCAT('Critical lab result reported (order_test_id=', NEW.order_test_id, ')'));
    END IF;
END$$

DELIMITER ;