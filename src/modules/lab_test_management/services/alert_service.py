"""
alert_service.py  –  Alert generation and management.

SQL equivalent:
    • AFTER INSERT / AFTER UPDATE triggers that fire on critical results
    • Stored procedure: sp_create_alert()
"""

from db.mongo_connection import get_db
from utils.helpers import to_object_id, id_to_str, ids_to_str, now_utc
from utils.constants import (
    ALERT_SEV_LOW, ALERT_SEV_MEDIUM, ALERT_SEV_HIGH, ALERT_SEV_CRITICAL,
    ALERT_TYPE_CRITICAL_RESULT, ALERT_TYPE_DELAYED_ORDER,
    ALERT_TYPE_ABNORMAL_RESULT,
)


# ══════════════════════════════════════════════════════════════════════
#  TRIGGER-LIKE FUNCTIONS  (called by order_service automatically)
# ══════════════════════════════════════════════════════════════════════
def trigger_critical_result_alert(order_id, result_value, test):
    """
    AFTER UPDATE trigger equivalent:
    When a result value is recorded and it falls outside the critical range,
    automatically create a 'Critical Result' alert.
    """
    low  = test.get("normal_range_min", 0)
    high = test.get("normal_range_max", 0)
    critical_low  = low  - (high - low)
    critical_high = high + (high - low)

    if result_value < critical_low or result_value > critical_high:
        severity = ALERT_SEV_CRITICAL
        msg = (f"🚨 CRITICAL: Test '{test['test_name']}' result = {result_value} "
               f"{test.get('unit','')}. Normal range: {low}–{high}.")
        create_alert(order_id, ALERT_TYPE_CRITICAL_RESULT, severity, msg)
        return True

    elif result_value < low or result_value > high:
        severity = ALERT_SEV_MEDIUM
        msg = (f"⚠️ ABNORMAL: Test '{test['test_name']}' result = {result_value} "
               f"{test.get('unit','')}. Normal range: {low}–{high}.")
        create_alert(order_id, ALERT_TYPE_ABNORMAL_RESULT, severity, msg)
        return True

    return False


def trigger_delayed_order_alert(order_id, hours_elapsed, expected_hours, test_name):
    """
    Periodic check trigger equivalent:
    If turnaround time exceeds expected hours, fire an alert.
    """
    severity = ALERT_SEV_HIGH
    msg = (f"⏰ DELAYED: Test '{test_name}' has been pending for "
           f"{hours_elapsed:.1f}h (expected: {expected_hours}h).")
    create_alert(order_id, ALERT_TYPE_DELAYED_ORDER, severity, msg)
    return True


# ══════════════════════════════════════════════════════════════════════
#  CRUD FOR ALERTS
# ══════════════════════════════════════════════════════════════════════
def create_alert(order_id, alert_type, severity, message):
    """Insert a new alert document."""
    doc = {
        "order_id":   to_object_id(order_id),
        "alert_type": alert_type,
        "severity":   severity,
        "message":    message,
        "created_at": now_utc(),
        "resolved":   False,
        "resolved_at": None,
    }
    result = get_db().alerts.insert_one(doc)
    print(f"  🔔 Alert created: {alert_type} – {severity}")
    return result.inserted_id


def resolve_alert(alert_id):
    """Mark an alert as resolved (equivalent to UPDATE with SET resolved=TRUE)."""
    result = get_db().alerts.update_one(
        {"_id": to_object_id(alert_id)},
        {"$set": {"resolved": True, "resolved_at": now_utc()}},
    )
    return result.modified_count


def get_unresolved_alerts():
    """Fetch all unresolved alerts, newest first."""
    docs = list(
        get_db().alerts.find({"resolved": False}).sort("created_at", -1)
    )
    return ids_to_str(docs)


def get_alerts_by_order(order_id):
    """Fetch all alerts for a specific order."""
    docs = list(
        get_db().alerts.find({"order_id": to_object_id(order_id)})
    )
    return ids_to_str(docs)


def get_all_alerts():
    """Return every alert, newest first."""
    docs = list(get_db().alerts.find().sort("created_at", -1))
    return ids_to_str(docs)


def count_alerts(resolved=None):
    """Count alerts, optionally filtered by resolved status."""
    filt = {}
    if resolved is not None:
        filt["resolved"] = resolved
    return get_db().alerts.count_documents(filt)
