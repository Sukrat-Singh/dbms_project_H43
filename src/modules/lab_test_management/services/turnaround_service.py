"""
turnaround_service.py  –  Turnaround time monitoring.

SQL equivalent:
    • Scheduled job / cron trigger that checks pending orders
    • Stored procedure: sp_check_turnaround()
    • SELECT … WHERE TIMESTAMPDIFF(HOUR, ordered_at, NOW()) > expected
"""

from db.mongo_connection import get_db
from utils.helpers import to_object_id, now_utc, hours_between, ids_to_str
from utils.constants import (
    ORDER_STATUS_COMPLETED, ORDER_STATUS_CANCELLED,
    TURNAROUND_WARNING_FACTOR, TURNAROUND_CRITICAL_FACTOR,
)
from services.alert_service import trigger_delayed_order_alert


# ══════════════════════════════════════════════════════════════════════
#  TURNAROUND CALCULATIONS
# ══════════════════════════════════════════════════════════════════════
def calculate_turnaround(order):
    """
    Calculate the turnaround time (in hours) for a single order.
    If the order is completed, use completed_at; otherwise use now.
    """
    start = order.get("ordered_at")
    end   = order.get("completed_at") or now_utc()
    return hours_between(start, end)


def get_turnaround_report():
    """
    Aggregation pipeline equivalent to:
        SELECT t.test_name,
               AVG(TIMESTAMPDIFF(HOUR, o.ordered_at, o.completed_at)) AS avg_tat,
               MIN(…) AS min_tat, MAX(…) AS max_tat, COUNT(*) AS total
        FROM lab_orders o
        JOIN lab_tests t ON o.test_id = t.id
        WHERE o.status = 'Completed'
        GROUP BY t.test_name;
    """
    pipeline = [
        {"$match": {"status": ORDER_STATUS_COMPLETED, "completed_at": {"$ne": None}}},
        {"$addFields": {
            "tat_hours": {
                "$divide": [
                    {"$subtract": ["$completed_at", "$ordered_at"]},
                    3600000,   # milliseconds → hours
                ]
            }
        }},
        {"$lookup": {
            "from": "lab_tests",
            "localField": "test_id",
            "foreignField": "_id",
            "as": "test_info",
        }},
        {"$unwind": "$test_info"},
        {"$group": {
            "_id": "$test_info.test_name",
            "avg_tat":   {"$avg": "$tat_hours"},
            "min_tat":   {"$min": "$tat_hours"},
            "max_tat":   {"$max": "$tat_hours"},
            "total":     {"$sum": 1},
            "expected":  {"$first": "$test_info.turnaround_hours"},
        }},
        {"$project": {
            "_id": 0,
            "test_name":     "$_id",
            "avg_tat":       {"$round": ["$avg_tat", 2]},
            "min_tat":       {"$round": ["$min_tat", 2]},
            "max_tat":       {"$round": ["$max_tat", 2]},
            "total_orders":  "$total",
            "expected_hours": "$expected",
        }},
        {"$sort": {"test_name": 1}},
    ]
    return list(get_db().lab_orders.aggregate(pipeline))


# ══════════════════════════════════════════════════════════════════════
#  DELAYED-ORDER CHECKER  (scheduled trigger equivalent)
# ══════════════════════════════════════════════════════════════════════
def check_delayed_orders():
    """
    Scan all non-terminal orders and fire alerts for any that exceed
    the expected turnaround time.  Call this periodically.
    """
    db = get_db()
    active_orders = list(db.lab_orders.find({
        "status": {"$nin": [ORDER_STATUS_COMPLETED, ORDER_STATUS_CANCELLED]}
    }))

    delayed = []
    for order in active_orders:
        test = db.lab_tests.find_one({"_id": order["test_id"]})
        if test is None:
            continue

        elapsed = hours_between(order["ordered_at"], now_utc())
        expected = test.get("turnaround_hours", 24)

        if elapsed and elapsed >= expected * TURNAROUND_CRITICAL_FACTOR:
            trigger_delayed_order_alert(
                order["_id"], elapsed, expected, test["test_name"]
            )
            delayed.append({
                "order_id":  str(order["_id"]),
                "test_name": test["test_name"],
                "elapsed_h": round(elapsed, 2),
                "expected_h": expected,
            })

    print(f"  ⏰ Checked {len(active_orders)} active orders → {len(delayed)} delayed")
    return delayed
