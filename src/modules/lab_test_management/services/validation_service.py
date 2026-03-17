"""
validation_service.py  –  Data validation layer.

SQL equivalent:
    • CHECK constraints
    • BEFORE INSERT / BEFORE UPDATE triggers
    • Stored procedures that validate input
"""

from models.patient_model import get_patient_by_id
from models.lab_test_model import get_test_by_id
from utils.constants import VALID_GENDERS, VALID_PRIORITIES, VALID_ORDER_STATUSES


def validate_patient_data(name, age, gender, contact):
    """
    Validate patient data before insertion.
    Equivalent to a BEFORE INSERT trigger on the patients table.
    """
    errors = []

    if not name or not name.strip():
        errors.append("Patient name is required")
    if not isinstance(age, (int, float)) or age < 0 or age > 150:
        errors.append("Age must be between 0 and 150")
    if gender not in VALID_GENDERS:
        errors.append(f"Gender must be one of {VALID_GENDERS}")
    if not contact or len(contact) < 10:
        errors.append("Contact must be at least 10 digits")

    return {"valid": len(errors) == 0, "errors": errors}


def validate_order_data(patient_id, test_id, priority):
    """
    Validate an order before placement.
    Equivalent to a BEFORE INSERT trigger with FK checks.
    """
    errors = []

    # FK existence check  (like  REFERENCES patients(id))
    patient = get_patient_by_id(patient_id)
    if patient is None:
        errors.append(f"Patient with ID '{patient_id}' does not exist")

    test = get_test_by_id(test_id)
    if test is None:
        errors.append(f"Lab test with ID '{test_id}' does not exist")

    if priority not in VALID_PRIORITIES:
        errors.append(f"Priority must be one of {VALID_PRIORITIES}")

    return {"valid": len(errors) == 0, "errors": errors, "patient": patient, "test": test}


def validate_status_transition(current_status, new_status):
    """
    Enforce valid status transitions.
    Equivalent to a CHECK constraint or BEFORE UPDATE trigger.
    
    Valid transitions:
        Pending → Sample Collected → Processing → Completed
        Any status → Cancelled
    """
    allowed_transitions = {
        "Pending":          ["Sample Collected", "Cancelled"],
        "Sample Collected": ["Processing", "Cancelled"],
        "Processing":       ["Completed", "Cancelled"],
        "Completed":        [],           # terminal state
        "Cancelled":        [],           # terminal state
    }

    if new_status not in VALID_ORDER_STATUSES:
        return {"valid": False, "error": f"Invalid status: {new_status}"}

    allowed = allowed_transitions.get(current_status, [])
    if new_status not in allowed:
        return {
            "valid": False,
            "error": f"Cannot transition from '{current_status}' to '{new_status}'. "
                     f"Allowed: {allowed}",
        }

    return {"valid": True, "error": None}


def validate_result_value(result_value, test):
    """
    Check whether a result is normal, abnormal, or critical.
    Returns a classification string.
    """
    if result_value is None:
        return "No Result"

    low  = test.get("normal_range_min", 0)
    high = test.get("normal_range_max", 0)

    # Critical: more than 2× outside normal range
    critical_low  = low  - (high - low)
    critical_high = high + (high - low)

    if critical_low > result_value or result_value > critical_high:
        return "Critical"
    elif low <= result_value <= high:
        return "Normal"
    else:
        return "Abnormal"
