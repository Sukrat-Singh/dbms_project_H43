"""
constants.py  –  Enums and constants for the Lab Test Management System.
Maps to SQL ENUM / CHECK constraints but enforced at the application level.
"""

# ── Order Status (mirrors a SQL ENUM column) ──────────────────────────
ORDER_STATUS_PENDING    = "Pending"
ORDER_STATUS_SAMPLE     = "Sample Collected"
ORDER_STATUS_PROCESSING = "Processing"
ORDER_STATUS_COMPLETED  = "Completed"
ORDER_STATUS_CANCELLED  = "Cancelled"

VALID_ORDER_STATUSES = [
    ORDER_STATUS_PENDING,
    ORDER_STATUS_SAMPLE,
    ORDER_STATUS_PROCESSING,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_CANCELLED,
]

# ── Priority Levels ───────────────────────────────────────────────────
PRIORITY_ROUTINE  = "Routine"
PRIORITY_URGENT   = "Urgent"
PRIORITY_CRITICAL = "Critical"

VALID_PRIORITIES = [PRIORITY_ROUTINE, PRIORITY_URGENT, PRIORITY_CRITICAL]

# ── Lab Test Categories ───────────────────────────────────────────────
CATEGORY_HEMATOLOGY    = "Hematology"
CATEGORY_BIOCHEMISTRY  = "Biochemistry"
CATEGORY_MICROBIOLOGY  = "Microbiology"
CATEGORY_IMMUNOLOGY    = "Immunology"
CATEGORY_PATHOLOGY     = "Pathology"
CATEGORY_RADIOLOGY     = "Radiology"

VALID_CATEGORIES = [
    CATEGORY_HEMATOLOGY,
    CATEGORY_BIOCHEMISTRY,
    CATEGORY_MICROBIOLOGY,
    CATEGORY_IMMUNOLOGY,
    CATEGORY_PATHOLOGY,
    CATEGORY_RADIOLOGY,
]

# ── Gender ────────────────────────────────────────────────────────────
VALID_GENDERS = ["Male", "Female", "Other"]

# ── Alert Severities ──────────────────────────────────────────────────
ALERT_SEV_LOW      = "Low"
ALERT_SEV_MEDIUM   = "Medium"
ALERT_SEV_HIGH     = "High"
ALERT_SEV_CRITICAL = "Critical"

VALID_ALERT_SEVERITIES = [ALERT_SEV_LOW, ALERT_SEV_MEDIUM, ALERT_SEV_HIGH, ALERT_SEV_CRITICAL]

# ── Alert Types ───────────────────────────────────────────────────────
ALERT_TYPE_CRITICAL_RESULT = "Critical Result"
ALERT_TYPE_DELAYED_ORDER   = "Delayed Order"
ALERT_TYPE_ABNORMAL_RESULT = "Abnormal Result"

VALID_ALERT_TYPES = [
    ALERT_TYPE_CRITICAL_RESULT,
    ALERT_TYPE_DELAYED_ORDER,
    ALERT_TYPE_ABNORMAL_RESULT,
]

# ── Turnaround Thresholds (hours) ────────────────────────────────────
TURNAROUND_WARNING_FACTOR  = 0.8   # 80% of expected → warning
TURNAROUND_CRITICAL_FACTOR = 1.0   # 100% exceeded  → alert
