-- queries/queries.sql
-- Example queries for module 43

-- 1. Patient lab history (latest results)
SELECT * FROM (
    SELECT p.patient_id, p.name, o.order_id, o.order_date, t.test_name, lr.result_value, lr.flag, lr.result_date
    FROM Patient p
    JOIN LabOrder o ON p.patient_id = o.patient_id
    JOIN OrderTest ot ON ot.order_id = o.order_id
    JOIN LabTest t ON t.test_id = ot.test_id
    LEFT JOIN LabResult lr ON lr.order_test_id = ot.order_test_id
    ORDER BY lr.result_date DESC
) AS hh LIMIT 200;

-- 2. Tests ordered TODAY
SELECT lt.test_name, COUNT(*) AS num_orders
FROM LabTest lt
JOIN OrderTest ot ON ot.test_id = lt.test_id
JOIN LabOrder o ON o.order_id = ot.order_id
WHERE DATE(o.order_date) = CURDATE()
GROUP BY lt.test_name
ORDER BY num_orders DESC;

-- 3. Pending (not yet reported) tests
SELECT o.order_id, p.name, lt.test_name, ot.order_test_id
FROM OrderTest ot
JOIN LabOrder o ON o.order_id = ot.order_id
JOIN LabTest lt ON lt.test_id = ot.test_id
JOIN Patient p ON p.patient_id = o.patient_id
WHERE ot.result_status = 'Pending';

-- 4. Most frequently ordered tests (top 10)
SELECT lt.test_name, COUNT(*) AS frequency
FROM OrderTest ot
JOIN LabTest lt ON lt.test_id = ot.test_id
GROUP BY lt.test_name
ORDER BY frequency DESC
LIMIT 10;

-- 5. Average turnaround per test (minutes)
SELECT lt.test_name, ROUND(AVG(tr.time_taken_minutes),1) AS avg_minutes
FROM Turnaround tr
JOIN OrderTest ot ON ot.order_test_id = tr.order_test_id
JOIN LabTest lt ON lt.test_id = ot.test_id
GROUP BY lt.test_name
ORDER BY avg_minutes DESC;

-- 6. Tests that require fasting
SELECT test_name, category, cost
FROM LabTest lt
JOIN Preparation p ON p.preparation_id = lt.preparation_id
WHERE p.fasting_required = TRUE;

-- 7. Lab utilization by day (orders per day last 14 days)
SELECT DATE(o.order_date) AS order_day, COUNT(*) AS orders
FROM LabOrder o
WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
GROUP BY order_day
ORDER BY order_day DESC;

-- 8. Patients with highest number of tests in last 30 days
SELECT p.patient_id, p.name, COUNT(*) AS tests_count
FROM Patient p
JOIN LabOrder o ON o.patient_id = p.patient_id
JOIN OrderTest ot ON ot.order_id = o.order_id
WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY p.patient_id, p.name
ORDER BY tests_count DESC
LIMIT 10;

-- 9. Tests ordered but no result recorded yet
SELECT ot.order_test_id, o.order_id, p.name, lt.test_name
FROM OrderTest ot
JOIN LabOrder o ON o.order_id = ot.order_id
JOIN Patient p ON p.patient_id = o.patient_id
JOIN LabTest lt ON lt.test_id = ot.test_id
LEFT JOIN LabResult lr ON lr.order_test_id = ot.order_test_id
WHERE lr.result_id IS NULL;

-- 10. Average cost per order (for billing analysis)
SELECT o.order_id, p.name,
       IFNULL(SUM(lt.cost),0) AS total_cost
FROM LabOrder o
JOIN Patient p ON p.patient_id = o.patient_id
JOIN OrderTest ot ON ot.order_id = o.order_id
JOIN LabTest lt ON lt.test_id = ot.test_id
GROUP BY o.order_id, p.name
ORDER BY total_cost DESC
LIMIT 50;

-- 11. Tests with turnaround greater than expected (slower than expected)
SELECT o.order_id, lt.test_name, tr.time_taken_minutes, lt.expected_turnaround_minutes
FROM Turnaround tr
JOIN OrderTest ot ON ot.order_test_id = tr.order_test_id
JOIN LabTest lt ON lt.test_id = ot.test_id
JOIN LabOrder o ON o.order_id = ot.order_id
WHERE tr.time_taken_minutes > lt.expected_turnaround_minutes;

-- 12. Critical results (from Alerts)
SELECT a.alert_id, a.order_test_id, a.alert_type, a.message, a.created_at
FROM Alerts a
ORDER BY a.created_at DESC;

-- 13. View: PatientLabSummary (create once; useful for UI)
DROP VIEW IF EXISTS PatientLabSummary;
CREATE VIEW PatientLabSummary AS
SELECT p.patient_id, p.name, o.order_id, o.order_date, lt.test_name,
       ot.order_test_id, lr.result_value, lr.numeric_value, lr.unit, lr.flag, lr.result_date
FROM Patient p
JOIN LabOrder o ON o.patient_id = p.patient_id
JOIN OrderTest ot ON ot.order_id = o.order_id
JOIN LabTest lt ON lt.test_id = ot.test_id
LEFT JOIN LabResult lr ON lr.order_test_id = ot.order_test_id;

-- 14. Top 5 slowest tests by average turnaround
SELECT lt.test_name, ROUND(AVG(tr.time_taken_minutes),1) AS avg_minutes
FROM Turnaround tr
JOIN OrderTest ot ON ot.order_test_id = tr.order_test_id
JOIN LabTest lt ON lt.test_id = ot.test_id
GROUP BY lt.test_name
ORDER BY avg_minutes DESC
LIMIT 5;

-- 15. Count tests per category
SELECT category, COUNT(*) AS tests_in_category
FROM LabTest
GROUP BY category;

-- 16. Recent results (last 7 days)
SELECT p.name, lt.test_name, lr.result_value, lr.flag, lr.result_date
FROM LabResult lr
JOIN OrderTest ot ON ot.order_test_id = lr.order_test_id
JOIN LabOrder o ON o.order_id = ot.order_id
JOIN Patient p ON p.patient_id = o.patient_id
JOIN LabTest lt ON lt.test_id = ot.test_id
WHERE lr.result_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY lr.result_date DESC;

-- 17. Tests without defined preparation
SELECT test_id, test_name FROM LabTest WHERE preparation_id IS NULL;

-- 18. Number of tests performed per technician/reporter (reported_by)
SELECT lr.reported_by, COUNT(*) AS reported_count
FROM LabResult lr
GROUP BY lr.reported_by
ORDER BY reported_count DESC;

-- 19. Workload: samples collected but not yet reported
SELECT o.order_id, p.name, lt.test_name, ot.sample_collected_at
FROM OrderTest ot
JOIN LabOrder o ON o.order_id = ot.order_id
JOIN Patient p ON p.patient_id = o.patient_id
JOIN LabTest lt ON lt.test_id = ot.test_id
LEFT JOIN LabResult lr ON lr.order_test_id = ot.order_test_id
WHERE ot.sample_collected = TRUE AND lr.result_id IS NULL;

-- 20. Example analytic: percentage of orders completed within expected turnaround for each test
SELECT
    lt.test_name,
    ROUND(100 * SUM(case when tr.time_taken_minutes <= lt.expected_turnaround_minutes then 1 else 0 end) / COUNT(tr.turnaround_id),1) AS pct_within_expected
FROM Turnaround tr
JOIN OrderTest ot ON ot.order_test_id = tr.order_test_id
JOIN LabTest lt ON lt.test_id = ot.test_id
GROUP BY lt.test_name
ORDER BY pct_within_expected DESC;

-- End of queries.sql