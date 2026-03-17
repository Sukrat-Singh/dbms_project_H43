# SQL to MongoDB Mapping – Lab Test Management System

This document maps every SQL concept used in the project to its MongoDB equivalent.

---

## 1. Data Definition (DDL)

| SQL Concept | MongoDB Equivalent | Our Implementation |
|---|---|---|
| `CREATE TABLE` | `db.create_collection()` | `mongo_connection.py` → `setup_collections()` |
| Column types (`INT`, `VARCHAR`, etc.) | JSON Schema Validator | `mongo_connection.py` → `PATIENT_VALIDATOR`, etc. |
| `NOT NULL` | `required` array in JSON Schema | All validator definitions |
| `CHECK` constraint | `minimum`, `maximum`, `enum` in JSON Schema | e.g., `age: min=0, max=150` |
| `UNIQUE` constraint | `create_index(unique=True)` | `test_name`, `contact` indexes |
| `FOREIGN KEY REFERENCES` | Application-level check | `validation_service.py` → `validate_order_data()` |
| `CREATE INDEX` | `create_index()` | All collections have indexes |
| `ENUM` type | `enum` in JSON Schema | `status`, `priority`, `gender`, `category` |

---

## 2. Data Manipulation (DML)

| SQL | MongoDB (pymongo) | Our Implementation |
|---|---|---|
| `INSERT INTO patients VALUES (...)` | `db.patients.insert_one({...})` | `patient_model.py` → `create_patient()` |
| `SELECT * FROM patients WHERE id = ?` | `db.patients.find_one({"_id": ObjectId(?)})` | `patient_model.py` → `get_patient_by_id()` |
| `SELECT * FROM patients ORDER BY name` | `db.patients.find().sort("name", 1)` | `patient_model.py` → `get_all_patients()` |
| `SELECT * FROM patients WHERE name LIKE '%x%'` | `db.patients.find({"name": {"$regex": "x", "$options": "i"}})` | `patient_model.py` → `search_patients()` |
| `UPDATE patients SET ... WHERE id = ?` | `db.patients.update_one({"_id": ?}, {"$set": {...}})` | `patient_model.py` → `update_patient()` |
| `DELETE FROM patients WHERE id = ?` | `db.patients.delete_one({"_id": ?})` | `patient_model.py` → `delete_patient()` |
| `SELECT COUNT(*) FROM patients` | `db.patients.count_documents({})` | `patient_model.py` → `count_patients()` |

---

## 3. Aggregation (GROUP BY, JOIN, etc.)

| SQL Query | MongoDB Aggregation Stage(s) | File |
|---|---|---|
| `GROUP BY category` | `$group: {_id: "$category"}` | `analytics_queries.py` |
| `COUNT(*)` | `$sum: 1` inside `$group` | `analytics_queries.py` |
| `AVG(column)` | `$avg: "$column"` | `turnaround_service.py` |
| `MIN / MAX` | `$min / $max` | `turnaround_service.py` |
| `SUM(cost)` | `$sum: "$test.cost"` | `analytics_queries.py` → `revenue_by_test()` |
| `JOIN ... ON` | `$lookup` stage | `report_queries.py`, `turnaround_service.py` |
| `WHERE` clause | `$match` stage | Throughout all queries |
| `ORDER BY` | `$sort` stage | Throughout all queries |
| `HAVING` | `$match` after `$group` | Used implicitly |
| `DATE_FORMAT(col, '%Y-%m')` | `$year`, `$month`, `$concat` | `analytics_queries.py` → `monthly_order_trends()` |
| `LEFT JOIN` | `$lookup` + `preserveNullAndEmptyArrays` | `report_queries.py` → `patient_full_report()` |
| `CASE WHEN ... THEN` | `$cond` | `analytics_queries.py`, `alert_queries.py` |

---

## 4. Triggers & Stored Procedures

| SQL Concept | MongoDB / Python Equivalent | Our Implementation |
|---|---|---|
| `BEFORE INSERT` trigger | Validation function called before `insert_one()` | `validation_service.py` → `validate_patient_data()` |
| `BEFORE UPDATE` trigger | Status transition check before `update_one()` | `validation_service.py` → `validate_status_transition()` |
| `AFTER INSERT` trigger | Function called right after `insert_one()` | `order_service.py` → auto-alert on critical result |
| `AFTER UPDATE` trigger | Function called right after `update_one()` | `alert_service.py` → `trigger_critical_result_alert()` |
| Stored Procedure `sp_place_order()` | Python function with validation + insert | `order_service.py` → `place_order()` |
| Stored Procedure `sp_record_result()` | Python function with insert + trigger | `order_service.py` → `record_result()` |
| Scheduled Job / Cron Trigger | Python function called periodically | `turnaround_service.py` → `check_delayed_orders()` |
| `TRANSACTION` (BEGIN...COMMIT) | Sequential operations with error handling | `order_service.py` → try/except blocks |

---

## 5. Constraints Summary

| SQL Constraint | MongoDB Implementation |
|---|---|
| `PRIMARY KEY` | `_id` field (auto-generated ObjectId) |
| `NOT NULL` | `required` in JSON Schema validator |
| `UNIQUE` | `unique=True` on index |
| `CHECK (age >= 0)` | `minimum: 0` in JSON Schema |
| `FOREIGN KEY` | Application-level: `validation_service.py` |
| `DEFAULT NOW()` | Set in Python: `now_utc()` during insert |
| `ENUM(...)` | `enum: [...]` in JSON Schema |

---

## Key Takeaway

> MongoDB lacks built-in triggers, stored procedures, and foreign key constraints.
> We implemented all of these at the **application level** using Python service functions,
> achieving the same data integrity guarantees as a relational database while maintaining
> MongoDB's flexibility and scalability advantages.
