"""
run_demo.py  –  Quick console demo to showcase all DBMS features.
Run this to test the entire system without the Streamlit dashboard.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.mongo_connection import setup_collections, get_db
from models.patient_model import create_patient, get_all_patients, search_patients
from models.lab_test_model import create_lab_test, get_all_tests
from models.order_model import get_all_orders
from services.order_service import place_order, advance_order_status, record_result
from services.turnaround_service import get_turnaround_report, check_delayed_orders
from services.alert_service import get_unresolved_alerts
from queries.analytics_queries import (
    tests_per_category, orders_by_status, revenue_by_test, patient_order_summary,
)
from queries.report_queries import test_result_summary
from queries.alert_queries import alerts_by_severity, alert_resolution_rate
from utils.helpers import format_currency


def hr(title=""):
    print(f"\n{'═'*60}")
    if title:
        print(f"  {title}")
        print(f"{'═'*60}")


def demo():
    db = get_db()

    # ── 0. Clean slate ──
    for c in ["patients", "lab_tests", "lab_orders", "alerts"]:
        db[c].delete_many({})
    setup_collections()

    # ── 1. Create Patients ──
    hr("1. INSERT – Patients")
    p1 = create_patient("Aarav Sharma", 32, "Male",   "9000000001", "aarav@mail.com")
    p2 = create_patient("Priya Patel",  28, "Female", "9000000002", "priya@mail.com")
    p3 = create_patient("Rohan Gupta",  45, "Male",   "9000000003", "rohan@mail.com")

    # ── 2. Create Lab Tests ──
    hr("2. INSERT – Lab Tests")
    t1 = create_lab_test("CBC",           "Hematology",    "cells/μL",
                         4500, 11000, 450, 6, "Complete Blood Count")
    t2 = create_lab_test("Blood Glucose", "Biochemistry",  "mg/dL",
                         70, 100, 200, 4, "Fasting blood sugar")
    t3 = create_lab_test("Lipid Profile", "Biochemistry",  "mg/dL",
                         0, 200, 800, 8, "Cholesterol & triglycerides")

    # ── 3. Place Orders (stored procedure) ──
    hr("3. STORED PROCEDURE – place_order()")
    o1 = place_order(p1, t1, "Routine",  "Routine check-up")
    o2 = place_order(p2, t2, "Urgent",   "Patient is diabetic")
    o3 = place_order(p3, t3, "Critical", "Chest pain reported")

    # ── 4. Advance Status (trigger: validates transitions) ──
    hr("4. TRIGGER – advance_order_status()")
    advance_order_status(str(o1), "Sample Collected")
    advance_order_status(str(o1), "Processing")

    # ── 5. Record Results (trigger: auto-alert on critical) ──
    hr("5. TRIGGER – record_result() → auto alert")
    record_result(str(o1), 8500)    # normal CBC
    record_result(str(o2), 250)     # high glucose → abnormal alert
    record_result(str(o3), 450)     # very high lipid → critical alert

    # ── 6. Queries ──
    hr("6. SELECT / GROUP BY – Analytics Queries")
    print("\nTests per category:")
    for row in tests_per_category():
        print(f"   {row['category']}: {row['total']}")

    print("\nOrders by status:")
    for row in orders_by_status():
        print(f"   {row['status']}: {row['total']}")

    print("\nRevenue by test:")
    for row in revenue_by_test():
        print(f"   {row['test_name']}: {format_currency(row['total_revenue'])} "
              f"({row['order_count']} orders)")

    print("\nPatient order summary:")
    for row in patient_order_summary():
        print(f"   {row['patient_name']}: {row['total_orders']} orders, "
              f"{row['completed']} completed")

    # ── 7. Turnaround Report ──
    hr("7. JOIN + AVG – Turnaround Report")
    for row in get_turnaround_report():
        print(f"   {row['test_name']}: avg {row['avg_tat']}h "
              f"(expected {row['expected_hours']}h, {row['total_orders']} orders)")

    # ── 8. Alerts ──
    hr("8. ALERTS – Unresolved")
    for a in get_unresolved_alerts():
        print(f"   [{a['severity']}] {a['message']}")

    print(f"\n   Alert Resolution Rate: {alert_resolution_rate()}")

    # ── 9. Search (LIKE equivalent) ──
    hr("9. SELECT … WHERE name LIKE '%rav%'")
    for p in search_patients("rav"):
        print(f"   Found: {p['name']} (Age: {p['age']})")

    hr("DEMO COMPLETE ✅")


if __name__ == "__main__":
    demo()
