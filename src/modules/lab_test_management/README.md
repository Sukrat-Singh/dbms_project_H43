# 🧪 Lab Test Management System

A comprehensive **MongoDB-based Lab Test Management System** built for the DBMS course project (H43).  
This module demonstrates how relational database concepts (tables, triggers, stored procedures, foreign keys, aggregation queries) can be implemented using **MongoDB Atlas** and **Python**.

---

## 📁 Project Structure

```
src/modules/lab_test_management/
│
├── db/
│   └── mongo_connection.py        # MongoDB Atlas connection + JSON Schema validators
│
├── models/                        # Collection schemas + CRUD (equivalent to SQL tables)
│   ├── patient_model.py
│   ├── lab_test_model.py
│   └── order_model.py
│
├── services/                      # ⭐ Triggers + Stored Procedures (application-level)
│   ├── order_service.py           # sp_place_order, sp_record_result
│   ├── turnaround_service.py      # Turnaround time monitoring
│   ├── alert_service.py           # AFTER INSERT/UPDATE trigger equivalents
│   └── validation_service.py      # BEFORE INSERT/UPDATE trigger equivalents
│
├── queries/                       # ⭐ Aggregation Pipelines (SQL query replacements)
│   ├── analytics_queries.py       # GROUP BY, COUNT, SUM, JOIN
│   ├── report_queries.py          # Multi-table JOINs for reports
│   └── alert_queries.py           # Alert analytics
│
├── utils/
│   ├── constants.py               # ENUMs and CHECK constraint values
│   └── helpers.py                 # ObjectId conversion, date formatting
│
├── sample_data/
│   └── seed_data.py               # Insert realistic sample data
│
├── dashboard/
│   └── app.py                     # ⭐ Streamlit interactive dashboard
│
├── demo/
│   └── run_demo.py                # Quick console demo
│
├── docs/                          # ⭐ Viva preparation
│   ├── schema_design.md           # Collection schemas with SQL equivalents
│   ├── sql_to_mongo_mapping.md    # Complete SQL → MongoDB mapping table
│   └── queries_explanation.md     # Every query explained step-by-step
│
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MongoDB Atlas account (free tier works)
- A `.env` file in the project root

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the project **root directory**:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=lab_test_management
```

### 3. Seed Sample Data
```bash
cd src/modules/lab_test_management
python -m sample_data.seed_data
```

### 4. Run the Dashboard
```bash
cd src/modules/lab_test_management
streamlit run dashboard/app.py
```

### 5. Run Console Demo
```bash
cd src/modules/lab_test_management
python -m demo.run_demo
```

---

## ⭐ Key DBMS Concepts Demonstrated

| SQL Concept | Implementation |
|---|---|
| CREATE TABLE | JSON Schema Validators in `mongo_connection.py` |
| FOREIGN KEY | Application-level checks in `validation_service.py` |
| BEFORE INSERT Trigger | `validation_service.py` → `validate_patient_data()` |
| AFTER UPDATE Trigger | `alert_service.py` → `trigger_critical_result_alert()` |
| Stored Procedure | `order_service.py` → `place_order()`, `record_result()` |
| GROUP BY + COUNT | `analytics_queries.py` → `tests_per_category()` |
| JOIN (multi-table) | `report_queries.py` → `patient_full_report()` |
| ENUM + CHECK | Constants + JSON Schema validators |
| Transaction | Sequential operations with validation in services |

---

## 📊 Dashboard Pages

1. **Dashboard** – KPI cards, order/test charts, active alerts
2. **Patients** – CRUD operations for patient records
3. **Lab Tests** – Test catalog management
4. **Orders** – Place orders, update status, record results
5. **Alerts** – View/resolve alerts, check for delayed orders
6. **Analytics** – Revenue, trends, turnaround time, alert metrics
7. **Reports** – Patient reports, test result summaries

---

## 👥 Team
- **Group:** H43
- **Course:** Database Management Systems

---

## 📝 License
This project is for academic purposes only.
