"""
app.py  –  Streamlit Dashboard for Lab Test Management System.
Run with:   streamlit run dashboard/app.py
From:       src/modules/lab_test_management/
"""

import os
import sys

# Add module root to sys.path so all imports resolve correctly
MODULE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MODULE_ROOT not in sys.path:
    sys.path.insert(0, MODULE_ROOT)

from datetime import datetime

import pandas as pd
import streamlit as st

# ── Internal imports ──────────────────────────────────────────────────
from db.mongo_connection import get_db, setup_collections
from models.lab_test_model import (
    count_tests,
    create_lab_test,
    delete_lab_test,
    get_all_tests,
    get_test_by_id,
)
from models.order_model import (
    count_orders,
    get_all_orders,
    get_orders_by_patient,
    get_orders_by_status,
)
from models.patient_model import (
    count_patients,
    create_patient,
    delete_patient,
    get_all_patients,
    get_patient_by_id,
    update_patient,
)
from queries.alert_queries import (
    alert_resolution_rate,
    alerts_by_severity,
    alerts_by_type,
)
from queries.analytics_queries import (
    monthly_order_trends,
    orders_by_priority,
    orders_by_status,
    patient_order_summary,
    revenue_by_test,
    tests_per_category,
)
from queries.report_queries import patient_full_report, test_result_summary
from services.alert_service import (
    count_alerts,
    get_all_alerts,
    get_unresolved_alerts,
    resolve_alert,
)
from services.order_service import advance_order_status, place_order, record_result
from services.turnaround_service import check_delayed_orders, get_turnaround_report
from utils.constants import VALID_CATEGORIES, VALID_GENDERS, VALID_PRIORITIES
from utils.helpers import format_currency, format_datetime

# ══════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Lab Test Management System",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure collections exist
setup_collections()


# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════
st.sidebar.title("🧪 Lab Test MGMT")
page = st.sidebar.radio(
    "Navigate",
    [
        "📊 Dashboard",
        "👤 Patients",
        "🔬 Lab Tests",
        "📋 Orders",
        "🔔 Alerts",
        "📈 Analytics",
        "📄 Reports",
    ],
)


# ══════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD (Overview)
# ══════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard Overview")
    st.markdown("---")

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👤 Total Patients", count_patients())
    col2.metric("🔬 Total Lab Tests", count_tests())
    col3.metric("📋 Total Orders", count_orders())
    col4.metric("🔔 Active Alerts", count_alerts(resolved=False))

    st.markdown("---")

    # Orders by Status chart
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Orders by Status")
        status_data = orders_by_status()
        if status_data:
            df = pd.DataFrame(status_data)
            st.bar_chart(df.set_index("status"))
        else:
            st.info("No orders yet.")

    with c2:
        st.subheader("Tests by Category")
        cat_data = tests_per_category()
        if cat_data:
            df = pd.DataFrame(cat_data)
            st.bar_chart(df.set_index("category"))
        else:
            st.info("No tests defined yet.")

    # Unresolved Alerts
    st.markdown("---")
    st.subheader("🚨 Unresolved Alerts")
    alerts = get_unresolved_alerts()
    if alerts:
        for a in alerts[:5]:
            severity_colors = {
                "Critical": "🔴",
                "High": "🟠",
                "Medium": "🟡",
                "Low": "🟢",
            }
            icon = severity_colors.get(a.get("severity"), "⚪")
            st.warning(f"{icon} **[{a['severity']}]** {a['message']}")
    else:
        st.success("✅ No unresolved alerts!")


# ══════════════════════════════════════════════════════════════════════
#  PAGE: PATIENTS
# ══════════════════════════════════════════════════════════════════════
elif page == "👤 Patients":
    st.title("👤 Patient Management")

    tab1, tab2 = st.tabs(["📋 View All", "➕ Add Patient"])

    with tab1:
        patients = get_all_patients()
        if patients:
            df = pd.DataFrame(patients)
            display_cols = ["_id", "name", "age", "gender", "contact", "email"]
            available = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available], use_container_width=True)

            # Delete patient
            st.markdown("---")
            st.subheader("🗑️ Delete Patient")
            pid = st.selectbox(
                "Select patient to delete",
                options=[p["_id"] for p in patients],
                format_func=lambda x: next(
                    (p["name"] for p in patients if p["_id"] == x), x
                ),
            )
            if st.button("Delete", key="del_patient"):
                delete_patient(pid)
                st.success("Patient deleted!")
                st.rerun()
        else:
            st.info("No patients found. Add one below!")

    with tab2:
        with st.form("add_patient"):
            st.subheader("Add New Patient")
            name = st.text_input("Full Name")
            age = st.number_input("Age", 0, 150, 25)
            gender = st.selectbox("Gender", VALID_GENDERS)
            contact = st.text_input("Contact (10+ digits)")
            email = st.text_input("Email")
            address = st.text_input("Address")
            history = st.text_input("Medical History (comma-separated)")
            submitted = st.form_submit_button("Create Patient")
            if submitted:
                try:
                    hist_list = (
                        [h.strip() for h in history.split(",") if h.strip()]
                        if history
                        else []
                    )
                    create_patient(
                        name, age, gender, contact, email, address, hist_list
                    )
                    st.success(f"✅ Patient '{name}' created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════
#  PAGE: LAB TESTS
# ══════════════════════════════════════════════════════════════════════
elif page == "🔬 Lab Tests":
    st.title("🔬 Lab Test Catalog")

    tab1, tab2 = st.tabs(["📋 View All", "➕ Add Test"])

    with tab1:
        tests = get_all_tests()
        if tests:
            df = pd.DataFrame(tests)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No lab tests defined. Add one below!")

    with tab2:
        with st.form("add_test"):
            st.subheader("Define New Lab Test")
            test_name = st.text_input("Test Name")
            category = st.selectbox("Category", VALID_CATEGORIES)
            desc = st.text_input("Description")
            unit = st.text_input("Unit (e.g. mg/dL)")
            range_min = st.number_input("Normal Range Min", value=0.0)
            range_max = st.number_input("Normal Range Max", value=100.0)
            cost = st.number_input("Cost (₹)", min_value=0.0, value=500.0)
            tat = st.number_input("Turnaround Hours", min_value=1, value=6)
            submitted = st.form_submit_button("Create Test")
            if submitted:
                try:
                    create_lab_test(
                        test_name, category, unit, range_min, range_max, cost, tat, desc
                    )
                    st.success(f"✅ Lab test '{test_name}' created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════
#  PAGE: ORDERS
# ══════════════════════════════════════════════════════════════════════
elif page == "📋 Orders":
    st.title("📋 Lab Orders")

    tab1, tab2, tab3 = st.tabs(["📋 View Orders", "➕ Place Order", "🧪 Record Result"])

    with tab1:
        orders = get_all_orders()
        if orders:
            df = pd.DataFrame(orders)
            st.dataframe(df, use_container_width=True)

            # Advance status
            st.markdown("---")
            st.subheader("🔄 Update Order Status")
            oid = st.selectbox("Select Order", [o["_id"] for o in orders])
            new_status = st.selectbox(
                "New Status",
                ["Sample Collected", "Processing", "Completed", "Cancelled"],
            )
            if st.button("Update Status"):
                try:
                    advance_order_status(oid, new_status)
                    st.success(f"Order updated to '{new_status}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No orders yet. Place one below!")

    with tab2:
        patients = get_all_patients()
        tests = get_all_tests()
        if not patients or not tests:
            st.warning("Add at least one patient and one lab test first!")
        else:
            with st.form("place_order"):
                st.subheader("Place New Order")
                patient = st.selectbox(
                    "Patient",
                    options=[p["_id"] for p in patients],
                    format_func=lambda x: next(
                        (p["name"] for p in patients if p["_id"] == x), x
                    ),
                )
                test = st.selectbox(
                    "Lab Test",
                    options=[t["_id"] for t in tests],
                    format_func=lambda x: next(
                        (t["test_name"] for t in tests if t["_id"] == x), x
                    ),
                )
                priority = st.selectbox("Priority", VALID_PRIORITIES)
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("Place Order")
                if submitted:
                    try:
                        place_order(patient, test, priority, notes)
                        st.success("✅ Order placed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab3:
        orders = get_all_orders()
        pending = [
            o
            for o in orders
            if o["status"] != "Completed" and o["status"] != "Cancelled"
        ]
        if not pending:
            st.info("No pending orders to record results for.")
        else:
            with st.form("record_result"):
                st.subheader("Record Lab Result")
                oid = st.selectbox("Select Order", options=[o["_id"] for o in pending])
                value = st.number_input("Result Value", value=0.0, format="%.2f")
                submitted = st.form_submit_button("Record Result")
                if submitted:
                    try:
                        result = record_result(oid, value)
                        st.success(
                            f"✅ Result recorded: {value} → "
                            f"**{result['classification']}**"
                        )
                        if result["alert_fired"]:
                            st.warning("🔔 An alert was automatically generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════
#  PAGE: ALERTS
# ══════════════════════════════════════════════════════════════════════
elif page == "🔔 Alerts":
    st.title("🔔 Alert Management")

    tab1, tab2 = st.tabs(["🚨 Unresolved", "📋 All Alerts"])

    with tab1:
        # Check for delayed orders
        if st.button("🔍 Check for Delayed Orders"):
            delayed = check_delayed_orders()
            if delayed:
                st.warning(f"Found {len(delayed)} delayed orders!")
            else:
                st.success("No delayed orders found.")

        alerts = get_unresolved_alerts()
        if alerts:
            for a in alerts:
                sev = a.get("severity", "Unknown")
                severity_colors = {
                    "Critical": "🔴",
                    "High": "🟠",
                    "Medium": "🟡",
                    "Low": "🟢",
                }
                icon = severity_colors.get(sev, "⚪")

                with st.expander(
                    f"{icon} [{sev}] {a.get('alert_type', '')} – "
                    f"{format_datetime(a.get('created_at'))}"
                ):
                    st.write(a["message"])
                    if st.button("✅ Resolve", key=f"resolve_{a['_id']}"):
                        resolve_alert(a["_id"])
                        st.success("Alert resolved!")
                        st.rerun()
        else:
            st.success("✅ No unresolved alerts!")

    with tab2:
        all_alerts = get_all_alerts()
        if all_alerts:
            df = pd.DataFrame(all_alerts)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No alerts in the system.")


# ══════════════════════════════════════════════════════════════════════
#  PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════════
elif page == "📈 Analytics":
    st.title("📈 Analytics & Insights")
    st.markdown("*MongoDB Aggregation Pipelines replacing SQL GROUP BY queries*")
    st.markdown("---")

    # Revenue
    st.subheader("💰 Revenue by Test")
    rev = revenue_by_test()
    if rev:
        df = pd.DataFrame(rev)
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("test_name")["total_revenue"])
    else:
        st.info("No completed orders with revenue data.")

    st.markdown("---")

    # Orders by Priority
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Orders by Priority")
        pri = orders_by_priority()
        if pri:
            df = pd.DataFrame(pri)
            st.bar_chart(df.set_index("priority"))
        else:
            st.info("No data.")

    with c2:
        st.subheader("📊 Alerts by Severity")
        sev = alerts_by_severity()
        if sev:
            df = pd.DataFrame(sev)
            st.bar_chart(df.set_index("severity"))
        else:
            st.info("No data.")

    st.markdown("---")

    # Monthly Trends
    st.subheader("📅 Monthly Order Trends")
    trends = monthly_order_trends()
    if trends:
        df = pd.DataFrame(trends)
        st.line_chart(df.set_index("month"))
    else:
        st.info("Not enough data for trends.")

    st.markdown("---")

    # Turnaround Report
    st.subheader("⏱️ Turnaround Time Report")
    tat = get_turnaround_report()
    if tat:
        df = pd.DataFrame(tat)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No completed orders yet.")

    # Alert Resolution
    st.markdown("---")
    st.subheader("📊 Alert Resolution Rate")
    rate = alert_resolution_rate()
    st.metric(
        "Resolution Rate",
        f"{rate.get('resolution_rate', 0)}%",
        f"{rate.get('resolved_alerts', 0)} / {rate.get('total_alerts', 0)}",
    )

    # Patient Summary
    st.markdown("---")
    st.subheader("👤 Patient Order Summary")
    summary = patient_order_summary()
    if summary:
        df = pd.DataFrame(summary)
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
#  PAGE: REPORTS
# ══════════════════════════════════════════════════════════════════════
elif page == "📄 Reports":
    st.title("📄 Reports")

    tab1, tab2 = st.tabs(["👤 Patient Report", "🧪 Test Result Summary"])

    with tab1:
        st.subheader("Patient Full Report")
        patients = get_all_patients()
        if patients:
            pid = st.selectbox(
                "Select Patient",
                options=[p["_id"] for p in patients],
                format_func=lambda x: next(
                    (p["name"] for p in patients if p["_id"] == x), x
                ),
            )
            if st.button("Generate Report"):
                report = patient_full_report(pid)
                if report:
                    st.subheader(f"Report for {report['name']}")
                    st.write(
                        f"**Age:** {report['age']}  |  **Gender:** {report['gender']}  |  **Contact:** {report['contact']}"
                    )

                    if report.get("orders"):
                        st.markdown("---")
                        st.subheader("Order History")
                        df = pd.DataFrame(report["orders"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No orders for this patient.")
                else:
                    st.warning("Patient not found.")
        else:
            st.info("Add patients first.")

    with tab2:
        st.subheader("Test Result Summary (Aggregate Stats)")
        summary = test_result_summary()
        if summary:
            df = pd.DataFrame(summary)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No results recorded yet.")


# ══════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════
st.sidebar.markdown("---")
st.sidebar.caption("Lab Test Management System  •  DBMS Project H43")
