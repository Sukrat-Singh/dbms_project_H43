# Queries Explanation – Lab Test Management System

This document explains every aggregation pipeline in the project with its SQL equivalent.

---

## 1. `analytics_queries.py`

### 1.1 `tests_per_category()`
**Purpose:** Count how many lab tests exist in each category.

**SQL:**
```sql
SELECT category, COUNT(*) AS total
FROM lab_tests
GROUP BY category
ORDER BY total DESC;
```

**MongoDB Pipeline:**
```python
[
    {"$group": {"_id": "$category", "total": {"$sum": 1}}},
    {"$project": {"_id": 0, "category": "$_id", "total": 1}},
    {"$sort": {"total": -1}},
]
```

**Explanation:**
- `$group` groups documents by `category` and counts each group
- `$project` renames `_id` to `category` for readability
- `$sort` orders results with the most popular category first

---

### 1.2 `revenue_by_test()`
**Purpose:** Calculate total revenue generated per test (only completed orders).

**SQL:**
```sql
SELECT t.test_name, t.cost, COUNT(o.id) AS order_count,
       SUM(t.cost) AS total_revenue
FROM lab_orders o
JOIN lab_tests t ON o.test_id = t.id
WHERE o.status = 'Completed'
GROUP BY t.test_name, t.cost
ORDER BY total_revenue DESC;
```

**MongoDB Pipeline:**
```python
[
    {"$match": {"status": "Completed"}},           # WHERE
    {"$lookup": {                                    # JOIN
        "from": "lab_tests",
        "localField": "test_id",
        "foreignField": "_id",
        "as": "test"
    }},
    {"$unwind": "$test"},                            # Flatten array
    {"$group": {                                     # GROUP BY
        "_id": "$test.test_name",
        "cost_per_test": {"$first": "$test.cost"},
        "order_count": {"$sum": 1},                  # COUNT
        "total_revenue": {"$sum": "$test.cost"}      # SUM
    }},
    {"$sort": {"total_revenue": -1}}                 # ORDER BY
]
```

---

### 1.3 `monthly_order_trends()`
**Purpose:** Show how many orders were placed each month.

**SQL:**
```sql
SELECT DATE_FORMAT(ordered_at, '%Y-%m') AS month,
       COUNT(*) AS total_orders
FROM lab_orders
GROUP BY month
ORDER BY month;
```

**MongoDB Pipeline:**
- Uses `$year` and `$month` to extract date parts
- `$concat` combines them into "YYYY-MM" format
- Groups by this computed month string

---

### 1.4 `patient_order_summary()`
**Purpose:** For each patient, show total orders and how many are completed.

**SQL:**
```sql
SELECT p.name, COUNT(o.id) AS total_orders,
       SUM(CASE WHEN o.status = 'Completed' THEN 1 ELSE 0 END) AS completed
FROM patients p
LEFT JOIN lab_orders o ON p.id = o.patient_id
GROUP BY p.name;
```

**MongoDB Pipeline:**
- `$lookup` performs a LEFT JOIN from patients to lab_orders
- `$size` counts total orders
- `$filter` + `$size` counts only completed orders (equivalent to `CASE WHEN`)

---

## 2. `report_queries.py`

### 2.1 `patient_full_report()`
**Purpose:** Generate a complete report for a single patient with all order history.

**SQL:**
```sql
SELECT p.*, o.*, t.test_name, t.unit, t.normal_range_min, t.normal_range_max
FROM patients p
JOIN lab_orders o ON p.id = o.patient_id
JOIN lab_tests t ON o.test_id = t.id
WHERE p.id = :patient_id
ORDER BY o.ordered_at DESC;
```

**MongoDB:** Uses two `$lookup` stages (double JOIN) to bring in both orders and test info.

---

### 2.2 `test_result_summary()`
**Purpose:** For each test type, show average, min, and max result values.

**SQL:**
```sql
SELECT t.test_name, COUNT(*), AVG(result_value), MIN(result_value), MAX(result_value)
FROM lab_orders o
JOIN lab_tests t ON o.test_id = t.id
WHERE result_value IS NOT NULL
GROUP BY t.test_name;
```

---

## 3. `alert_queries.py`

### 3.1 `unresolved_critical_alerts()`
**Purpose:** Get all unresolved, critical alerts with test details.

**SQL:**
```sql
SELECT a.*, t.test_name
FROM alerts a
JOIN lab_orders o ON a.order_id = o.id
JOIN lab_tests t ON o.test_id = t.id
WHERE a.resolved = FALSE AND a.severity = 'Critical';
```

**MongoDB:** Triple `$lookup` chain: alerts → orders → lab_tests.

---

### 3.2 `alert_resolution_rate()`
**Purpose:** Calculate what percentage of alerts have been resolved.

**SQL:**
```sql
SELECT COUNT(*) AS total,
       SUM(CASE WHEN resolved THEN 1 ELSE 0 END) AS resolved_count,
       ROUND(resolved_count * 100.0 / total, 2) AS rate
FROM alerts;
```

**MongoDB:**
- `$cond` replaces `CASE WHEN`
- `$divide` + `$multiply` replaces percentage calculation
- `$round` rounds to 2 decimal places

---

## 4. Turnaround Time Query

### `get_turnaround_report()` (in `turnaround_service.py`)
**Purpose:** Average turnaround time per test type.

**SQL:**
```sql
SELECT t.test_name,
       AVG(TIMESTAMPDIFF(HOUR, o.ordered_at, o.completed_at)) AS avg_tat,
       t.turnaround_hours AS expected
FROM lab_orders o
JOIN lab_tests t ON o.test_id = t.id
WHERE o.status = 'Completed'
GROUP BY t.test_name;
```

**MongoDB:**
- `$subtract` calculates the time difference in milliseconds
- `$divide` by 3,600,000 converts to hours
- `$avg` computes the average across all orders for each test

---

## Summary of MongoDB Stages Used

| Stage | SQL Equivalent | Times Used |
|---|---|---|
| `$match` | `WHERE` | 10+ |
| `$group` | `GROUP BY` | 8 |
| `$lookup` | `JOIN` | 7 |
| `$unwind` | Flatten JOIN results | 7 |
| `$project` | `SELECT` (column selection) | 10+ |
| `$sort` | `ORDER BY` | 10+ |
| `$sum` | `COUNT(*)` / `SUM()` | 8 |
| `$avg` | `AVG()` | 3 |
| `$min` / `$max` | `MIN()` / `MAX()` | 3 |
| `$cond` | `CASE WHEN` | 3 |
| `$addFields` | Computed columns | 2 |
| `$filter` | Subquery filter | 1 |
