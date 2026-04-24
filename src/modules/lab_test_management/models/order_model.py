"""
order_model.py  –  Lab Order collection & CRUD operations.

SQL equivalent:
    CREATE TABLE lab_orders (
        id           SERIAL PRIMARY KEY,
        patient_id   INT REFERENCES patients(id),
        test_id      INT REFERENCES lab_tests(id),
        status       ENUM('Pending','Sample Collected','Processing','Completed','Cancelled'),
        priority     ENUM('Routine','Urgent','Critical'),
        result_value FLOAT,
        ordered_at   TIMESTAMP DEFAULT NOW(),
        completed_at TIMESTAMP,
        notes        TEXT
    );
"""

from db.mongo_connection import get_db
from utils.helpers import to_object_id, id_to_str, ids_to_str, now_utc
from utils.constants import (
    VALID_ORDER_STATUSES, VALID_PRIORITIES,
    ORDER_STATUS_PENDING,
    PRIORITY_ROUTINE,
)


# ── CREATE ────────────────────────────────────────────────────────────
def create_order(patient_id, test_id, priority=PRIORITY_ROUTINE, notes=""):
    """
    Place a new lab order (status defaults to 'Pending').
    This is the INSERT equivalent; trigger-like side effects
    (alerts, turnaround checks) are handled by the service layer.
    """
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Priority must be one of {VALID_PRIORITIES}")

    doc = {
        "patient_id":   to_object_id(patient_id),
        "test_id":      to_object_id(test_id),
        "status":       ORDER_STATUS_PENDING,
        "priority":     priority,
        "result_value":  None,
        "ordered_at":   now_utc(),
        "completed_at": None,
        "notes":        notes,
    }
    result = get_db().lab_orders.insert_one(doc)
    print(f"  ✅ Order created (ID: {result.inserted_id})")
    return result.inserted_id


# ── READ ──────────────────────────────────────────────────────────────
def get_order_by_id(order_id):
    """Fetch a single order by _id."""
    doc = get_db().lab_orders.find_one({"_id": to_object_id(order_id)})
    return id_to_str(doc) if doc else None


def get_orders_by_patient(patient_id):
    """Get all orders for a specific patient."""
    docs = list(
        get_db().lab_orders.find({"patient_id": to_object_id(patient_id)})
        .sort("ordered_at", -1)
    )
    return ids_to_str(docs)


def get_orders_by_status(status):
    """Get all orders with a given status."""
    docs = list(get_db().lab_orders.find({"status": status}))
    return ids_to_str(docs)


def get_all_orders():
    """Return every order, newest first."""
    docs = list(get_db().lab_orders.find().sort("ordered_at", -1))
    return ids_to_str(docs)


# ── UPDATE ────────────────────────────────────────────────────────────
def update_order_status(order_id, new_status):
    """Advance an order to a new status."""
    if new_status not in VALID_ORDER_STATUSES:
        raise ValueError(f"Status must be one of {VALID_ORDER_STATUSES}")
    update = {"$set": {"status": new_status}}
    if new_status == "Completed":
        update["$set"]["completed_at"] = now_utc()
    result = get_db().lab_orders.update_one(
        {"_id": to_object_id(order_id)}, update
    )
    return result.modified_count


def set_result_value(order_id, value):
    """Record the numeric lab result on a completed order."""
    result = get_db().lab_orders.update_one(
        {"_id": to_object_id(order_id)},
        {"$set": {"result_value": float(value)}},
    )
    return result.modified_count


# ── DELETE ────────────────────────────────────────────────────────────
def delete_order(order_id):
    result = get_db().lab_orders.delete_one({"_id": to_object_id(order_id)})
    return result.deleted_count


# ── COUNT ─────────────────────────────────────────────────────────────
def count_orders(status=None):
    filt = {"status": status} if status else {}
    return get_db().lab_orders.count_documents(filt)
