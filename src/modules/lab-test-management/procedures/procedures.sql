-- procedures/procedures.sql
-- Run after schema.sql (and triggers if you want them active)

DELIMITER $$

-- 1) Get all tests and results for a patient
DROP PROCEDURE IF EXISTS get_patient_tests$$
CREATE PROCEDURE get_patient_tests(IN pid INT)
BEGIN
    SELECT
        o.order_id,
        o.order_date,
        o.ordered_by,
        ot.order_test_id,
        t.test_name,
        lr.result_value,
        lr.numeric_value,
        lr.unit,
        lr.flag,
        lr.result_date
    FROM LabOrder o
    JOIN OrderTest ot ON ot.order_id = o.order_id
    JOIN LabTest t ON t.test_id = ot.test_id
    LEFT JOIN LabResult lr ON lr.order_test_id = ot.order_test_id
    WHERE o.patient_id = pid
    ORDER BY o.order_date DESC, t.test_name;
END$$

-- 2) Average turnaround per test (returns test_name + avg minutes)
DROP PROCEDURE IF EXISTS turnaround_report$$
CREATE PROCEDURE turnaround_report()
BEGIN
    SELECT lt.test_id, lt.test_name, ROUND(AVG(tr.time_taken_minutes),1) AS avg_turnaround_minutes
    FROM Turnaround tr
    JOIN OrderTest ot ON ot.order_test_id = tr.order_test_id
    JOIN LabTest lt ON lt.test_id = ot.test_id
    GROUP BY lt.test_id, lt.test_name
    ORDER BY avg_turnaround_minutes DESC;
END$$

-- 3) Create a lab order for a patient and add exactly one test (call multiple times to add multiple tests)
-- Returns the new order_id in a SELECT
DROP PROCEDURE IF EXISTS create_lab_order_add_test$$
CREATE PROCEDURE create_lab_order_add_test(
    IN p_patient_id INT,
    IN p_ordered_by VARCHAR(120),
    IN p_test_id INT
)
BEGIN
    DECLARE new_order_id INT;
    -- Create order
    INSERT INTO LabOrder (patient_id, ordered_by, status) VALUES (p_patient_id, p_ordered_by, 'Ordered');
    SET new_order_id = LAST_INSERT_ID();

    -- Add test to order
    INSERT INTO OrderTest (order_id, test_id, sample_collected) VALUES (new_order_id, p_test_id, FALSE);

    SELECT new_order_id AS order_id;
END$$

-- 4) Insert a turnaround record for an order_test (this will compute time via trigger)
DROP PROCEDURE IF EXISTS create_turnaround$$
CREATE PROCEDURE create_turnaround(
    IN p_order_test_id INT,
    IN p_collection_time DATETIME,
    IN p_report_time DATETIME
)
BEGIN
    INSERT INTO Turnaround (order_test_id, collection_time, report_time)
    VALUES (p_order_test_id, p_collection_time, p_report_time);
END$$

DELIMITER ;