# Schema Design – Lab Test Management System

## Overview
This document describes the MongoDB collections (equivalent to SQL tables) used in the Lab Test Management System.

---

## 1. `patients` Collection

**SQL Equivalent:**
```sql
CREATE TABLE patients (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    age             INT CHECK (age >= 0 AND age <= 150),
    gender          ENUM('Male', 'Female', 'Other'),
    contact         VARCHAR(15) UNIQUE NOT NULL,
    email           VARCHAR(100),
    address         TEXT,
    medical_history TEXT[],
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**MongoDB Document Structure:**
```json
{
    "_id": ObjectId("..."),
    "name": "Aarav Sharma",
    "age": 32,
    "gender": "Male",
    "contact": "9876543210",
    "email": "aarav@email.com",
    "address": "12 MG Road, Delhi",
    "medical_history": ["Diabetes Type 2"],
    "created_at": ISODate("2026-03-18T00:00:00Z")
}
```

**Indexes:**
- `name` (ASCENDING) – for search queries
- `contact` (ASCENDING, UNIQUE) – prevents duplicate registrations

---

## 2. `lab_tests` Collection

**SQL Equivalent:**
```sql
CREATE TABLE lab_tests (
    id               SERIAL PRIMARY KEY,
    test_name        VARCHAR(100) UNIQUE NOT NULL,
    category         ENUM('Hematology', 'Biochemistry', 'Microbiology', 
                          'Immunology', 'Pathology', 'Radiology'),
    description      TEXT,
    unit             VARCHAR(20) NOT NULL,
    normal_range_min FLOAT NOT NULL,
    normal_range_max FLOAT NOT NULL,
    cost             FLOAT CHECK (cost >= 0),
    turnaround_hours INT CHECK (turnaround_hours >= 1)
);
```

**MongoDB Document Structure:**
```json
{
    "_id": ObjectId("..."),
    "test_name": "Complete Blood Count (CBC)",
    "category": "Hematology",
    "description": "Measures RBC, WBC, and platelets",
    "unit": "cells/μL",
    "normal_range_min": 4500.0,
    "normal_range_max": 11000.0,
    "cost": 450.0,
    "turnaround_hours": 6
}
```

**Indexes:**
- `test_name` (ASCENDING, UNIQUE)
- `category` (ASCENDING)

---

## 3. `lab_orders` Collection

**SQL Equivalent:**
```sql
CREATE TABLE lab_orders (
    id           SERIAL PRIMARY KEY,
    patient_id   INT REFERENCES patients(id),
    test_id      INT REFERENCES lab_tests(id),
    status       ENUM('Pending', 'Sample Collected', 'Processing', 'Completed', 'Cancelled'),
    priority     ENUM('Routine', 'Urgent', 'Critical'),
    result_value FLOAT,
    ordered_at   TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    notes        TEXT
);
```

**MongoDB Document Structure:**
```json
{
    "_id": ObjectId("..."),
    "patient_id": ObjectId("..."),
    "test_id": ObjectId("..."),
    "status": "Completed",
    "priority": "Urgent",
    "result_value": 250.0,
    "ordered_at": ISODate("2026-03-17T10:00:00Z"),
    "completed_at": ISODate("2026-03-17T14:00:00Z"),
    "notes": "Patient is diabetic"
}
```

**Indexes:**
- `patient_id` (ASCENDING) – fast lookup of orders per patient
- `test_id` (ASCENDING) – join support
- `status` (ASCENDING) – filter by status
- `ordered_at` (ASCENDING) – chronological sorting

---

## 4. `alerts` Collection

**SQL Equivalent:**
```sql
CREATE TABLE alerts (
    id          SERIAL PRIMARY KEY,
    order_id    INT REFERENCES lab_orders(id),
    alert_type  ENUM('Critical Result', 'Delayed Order', 'Abnormal Result'),
    severity    ENUM('Low', 'Medium', 'High', 'Critical'),
    message     TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    resolved    BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP
);
```

**MongoDB Document Structure:**
```json
{
    "_id": ObjectId("..."),
    "order_id": ObjectId("..."),
    "alert_type": "Critical Result",
    "severity": "Critical",
    "message": "CBC result = 25000 cells/μL. Normal: 4500–11000.",
    "created_at": ISODate("2026-03-17T14:00:00Z"),
    "resolved": false,
    "resolved_at": null
}
```

**Indexes:**
- `order_id` (ASCENDING)
- `resolved` (ASCENDING) – quickly find unresolved alerts

---

## Relationships (Foreign Key Equivalents)

```
patients  ──< lab_orders >──  lab_tests
                  │
                  └──< alerts
```

- `lab_orders.patient_id` → references `patients._id`
- `lab_orders.test_id` → references `lab_tests._id`
- `alerts.order_id` → references `lab_orders._id`

> **Note:** MongoDB does not enforce foreign keys at the database level. We enforce referential integrity at the **application level** using `validation_service.py`.
