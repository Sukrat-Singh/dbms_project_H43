"""
order_service.py  –  High-level order operations (stored procedures).

SQL equivalent:
    • Stored procedure: sp_place_order(patient_id, test_id, priority)
    • Stored procedure: sp_record_result(order_id, value)
    • Transaction blocks with COMMIT / ROLLBACK
    • AFTER INSERT / AFTER UPDATE triggers
"""

from models.order_model import (
    create_order, get_order_by_id,
    update_order_status, set_result_value,
)
from models.lab_test_model import get_test_by_id
from services.validation_service import (
    validate_order_data,
    validate_status_transition,
    validate_result_value,
)
from services.alert_service import trigger_critical_result_alert
from utils.helpers import to_object_id
from utils.constants import ORDER_STATUS_COMPLETED


# ══════════════════════════════════════════════════════════════════════
#  STORED PROCEDURE: sp_place_order
# ══════════════════════════════════════════════════════════════════════
def place_order(patient_id, test_id, priority="Routine", notes=""):
    """
    High-level procedure to place a lab order.
    Steps:
        1. Validate patient & test exist (FK check)
        2. Create the order document
        3. (Future) deduct inventory, notify lab, etc.

    Equivalent SQL:
        BEGIN TRANSACTION;
            -- validate
            SELECT 1 FROM patients WHERE id = :pid;
            SELECT 1 FROM lab_tests WHERE id = :tid;
            -- insert
            INSERT INTO lab_orders (...) VALUES (...);
        COMMIT;
    """
    # Step 1 – Validation (BEFORE INSERT trigger)
    validation = validate_order_data(patient_id, test_id, priority)
    if not validation["valid"]:
        raise ValueError(f"Order validation failed: {validation['errors']}")

    # Step 2 – Insert
    order_id = create_order(patient_id, test_id, priority, notes)
    print(f"  📋 Order placed successfully for patient "
          f"'{validation['patient']['name']}' → test "
          f"'{validation['test']['test_name']}'")
    return order_id


# ══════════════════════════════════════════════════════════════════════
#  STORED PROCEDURE: sp_advance_status
# ══════════════════════════════════════════════════════════════════════
def advance_order_status(order_id, new_status):
    """
    Advance an order's status with transition validation.
    Equivalent to an UPDATE with a BEFORE UPDATE trigger that checks
    allowed transitions.
    """
    order = get_order_by_id(order_id)
    if order is None:
        raise ValueError(f"Order '{order_id}' not found")

    check = validate_status_transition(order["status"], new_status)
    if not check["valid"]:
        raise ValueError(check["error"])

    update_order_status(order_id, new_status)
    print(f"  🔄 Order {order_id}: {order['status']} → {new_status}")
    return True


# ══════════════════════════════════════════════════════════════════════
#  STORED PROCEDURE: sp_record_result
# ══════════════════════════════════════════════════════════════════════
def record_result(order_id, result_value):
    """
    Record a lab result and automatically:
        1. Set the result value
        2. Mark status as Completed
        3. AFTER UPDATE trigger: check if result is critical / abnormal
           and fire an alert if needed.

    Equivalent SQL:
        BEGIN TRANSACTION;
            UPDATE lab_orders SET result_value = :val,
                   status = 'Completed', completed_at = NOW()
            WHERE id = :oid;
            -- AFTER UPDATE trigger fires here
            IF :val NOT BETWEEN normal_min AND normal_max THEN
                INSERT INTO alerts (...) VALUES (...);
            END IF;
        COMMIT;
    """
    order = get_order_by_id(order_id)
    if order is None:
        raise ValueError(f"Order '{order_id}' not found")

    # Fetch the test for range checking
    test = get_test_by_id(order["test_id"])
    if test is None:
        raise ValueError("Associated lab test not found")

    # Record value + mark completed
    set_result_value(order_id, result_value)
    update_order_status(order_id, ORDER_STATUS_COMPLETED)

    # AFTER UPDATE trigger – alert on abnormal / critical
    classification = validate_result_value(result_value, test)
    alert_fired = trigger_critical_result_alert(order_id, result_value, test)

    print(f"  🧪 Result recorded: {result_value} {test.get('unit','')} "
          f"→ {classification}")
    return {
        "order_id":       order_id,
        "result_value":   result_value,
        "classification": classification,
        "alert_fired":    alert_fired,
    }
