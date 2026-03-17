"""
seed_data.py  –  Populate the database with realistic sample data.
Run this once to have meaningful data for the dashboard and demo.
"""

import sys, os, random
from datetime import timedelta

# Add module root to path so imports work when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.mongo_connection import setup_collections, get_db
from models.patient_model import create_patient
from models.lab_test_model import create_lab_test
from models.order_model import create_order
from services.order_service import record_result
from utils.helpers import now_utc
from utils.constants import PRIORITY_ROUTINE, PRIORITY_URGENT, PRIORITY_CRITICAL


# ══════════════════════════════════════════════════════════════════════
#  SAMPLE DATA
# ══════════════════════════════════════════════════════════════════════
PATIENTS = [
    {"name": "Aarav Sharma",    "age": 32, "gender": "Male",   "contact": "9876543210",
     "email": "aarav@email.com",   "address": "12 MG Road, Delhi",
     "medical_history": ["Diabetes Type 2"]},
    {"name": "Priya Patel",     "age": 28, "gender": "Female", "contact": "9876543211",
     "email": "priya@email.com",   "address": "45 Park Street, Mumbai",
     "medical_history": []},
    {"name": "Rohan Gupta",     "age": 45, "gender": "Male",   "contact": "9876543212",
     "email": "rohan@email.com",   "address": "78 Brigade Road, Bangalore",
     "medical_history": ["Hypertension", "High Cholesterol"]},
    {"name": "Sneha Reddy",     "age": 55, "gender": "Female", "contact": "9876543213",
     "email": "sneha@email.com",   "address": "23 Anna Salai, Chennai",
     "medical_history": ["Thyroid"]},
    {"name": "Vikram Singh",    "age": 38, "gender": "Male",   "contact": "9876543214",
     "email": "vikram@email.com",  "address": "56 Civil Lines, Jaipur",
     "medical_history": []},
    {"name": "Ananya Iyer",     "age": 62, "gender": "Female", "contact": "9876543215",
     "email": "ananya@email.com",  "address": "89 Church Street, Kolkata",
     "medical_history": ["Asthma", "Diabetes Type 1"]},
    {"name": "Karan Mehta",     "age": 25, "gender": "Male",   "contact": "9876543216",
     "email": "karan@email.com",   "address": "34 Linking Road, Pune",
     "medical_history": []},
    {"name": "Divya Nair",      "age": 41, "gender": "Female", "contact": "9876543217",
     "email": "divya@email.com",   "address": "67 Residency Road, Hyderabad",
     "medical_history": ["PCOS"]},
]

LAB_TESTS = [
    {"test_name": "Complete Blood Count (CBC)", "category": "Hematology",
     "unit": "cells/μL", "normal_range_min": 4500.0, "normal_range_max": 11000.0,
     "cost": 450.0, "turnaround_hours": 6,
     "description": "Measures red blood cells, white blood cells, and platelets"},
    {"test_name": "Blood Glucose Fasting", "category": "Biochemistry",
     "unit": "mg/dL", "normal_range_min": 70.0, "normal_range_max": 100.0,
     "cost": 200.0, "turnaround_hours": 4,
     "description": "Measures blood sugar after an 8-hour fast"},
    {"test_name": "Lipid Profile", "category": "Biochemistry",
     "unit": "mg/dL", "normal_range_min": 0.0, "normal_range_max": 200.0,
     "cost": 800.0, "turnaround_hours": 8,
     "description": "Total cholesterol, HDL, LDL, triglycerides"},
    {"test_name": "Thyroid Panel (TSH)", "category": "Immunology",
     "unit": "mIU/L", "normal_range_min": 0.4, "normal_range_max": 4.0,
     "cost": 600.0, "turnaround_hours": 12,
     "description": "Thyroid stimulating hormone test"},
    {"test_name": "Liver Function Test (LFT)", "category": "Biochemistry",
     "unit": "U/L", "normal_range_min": 7.0, "normal_range_max": 56.0,
     "cost": 700.0, "turnaround_hours": 8,
     "description": "ALT, AST, ALP, bilirubin levels"},
    {"test_name": "Kidney Function Test (KFT)", "category": "Biochemistry",
     "unit": "mg/dL", "normal_range_min": 0.7, "normal_range_max": 1.3,
     "cost": 650.0, "turnaround_hours": 8,
     "description": "Creatinine, BUN, uric acid levels"},
    {"test_name": "Urine Culture", "category": "Microbiology",
     "unit": "CFU/mL", "normal_range_min": 0.0, "normal_range_max": 100000.0,
     "cost": 500.0, "turnaround_hours": 48,
     "description": "Detect bacteria or fungi in urine"},
    {"test_name": "HbA1c", "category": "Hematology",
     "unit": "%", "normal_range_min": 4.0, "normal_range_max": 5.6,
     "cost": 550.0, "turnaround_hours": 6,
     "description": "Average blood sugar over the past 2-3 months"},
]


def seed():
    """Wipe existing data (for development) and insert sample records."""
    db = get_db()

    # ── Wipe ──
    for col in ["patients", "lab_tests", "lab_orders", "alerts"]:
        db[col].delete_many({})
    print("🗑️  Cleared existing data\n")

    # ── Setup collections & validators ──
    setup_collections()

    # ── Patients ──
    print("\n── Inserting patients ──")
    patient_ids = []
    for p in PATIENTS:
        pid = create_patient(**p)
        patient_ids.append(pid)

    # ── Lab Tests ──
    print("\n── Inserting lab tests ──")
    test_ids = []
    for t in LAB_TESTS:
        tid = create_lab_test(**t)
        test_ids.append(tid)

    # ── Orders (some with results, some pending) ──
    print("\n── Creating lab orders ──")
    priorities = [PRIORITY_ROUTINE, PRIORITY_ROUTINE, PRIORITY_URGENT, PRIORITY_CRITICAL]
    order_ids = []

    for i in range(15):
        pid = random.choice(patient_ids)
        tid = random.choice(test_ids)
        pri = random.choice(priorities)
        oid = create_order(pid, tid, pri,"Seeded order")

        # Backdate some orders for realistic timestamps
        offset_hours = random.randint(1, 72)
        db.lab_orders.update_one(
            {"_id": oid},
            {"$set": {"ordered_at": now_utc() - timedelta(hours=offset_hours)}},
        )
        order_ids.append(oid)

    # ── Record results for ~60% of orders (triggers alerts automatically) ──
    print("\n── Recording results (triggers alerts on abnormal values) ──")
    for oid in order_ids[:9]:
        order = db.lab_orders.find_one({"_id": oid})
        test  = db.lab_tests.find_one({"_id": order["test_id"]})
        low   = test["normal_range_min"]
        high  = test["normal_range_max"]

        # Mix of normal, abnormal, and critical values
        roll = random.random()
        if roll < 0.5:
            value = round(random.uniform(low, high), 2)          # normal
        elif roll < 0.8:
            value = round(random.uniform(high, high * 1.5), 2)   # abnormal
        else:
            value = round(random.uniform(high * 2, high * 3), 2) # critical
        try:
            record_result(str(oid), value)
        except Exception as e:
            print(f"  ⚠️  Could not record result for order {oid}: {e}")

    # ── Summary ──
    print("\n" + "═" * 50)
    print(f"  Patients : {db.patients.count_documents({})}")
    print(f"  Lab Tests: {db.lab_tests.count_documents({})}")
    print(f"  Orders   : {db.lab_orders.count_documents({})}")
    print(f"  Alerts   : {db.alerts.count_documents({})}")
    print("═" * 50)
    print("✅  Seeding complete!\n")


if __name__ == "__main__":
    seed()
