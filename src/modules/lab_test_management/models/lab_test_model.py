"""
lab_test_model.py  –  Lab Test catalog collection & CRUD operations.

SQL equivalent:
    CREATE TABLE lab_tests (
        id               SERIAL PRIMARY KEY,
        test_name        VARCHAR(100) UNIQUE NOT NULL,
        category         ENUM('Hematology','Biochemistry',...),
        description      TEXT,
        unit             VARCHAR(20) NOT NULL,
        normal_range_min FLOAT NOT NULL,
        normal_range_max FLOAT NOT NULL,
        cost             FLOAT CHECK (cost >= 0),
        turnaround_hours INT CHECK (turnaround_hours >= 1)
    );
"""

from db.mongo_connection import get_db
from utils.helpers import to_object_id, id_to_str, ids_to_str
from utils.constants import VALID_CATEGORIES


# ── CREATE ────────────────────────────────────────────────────────────
def create_lab_test(test_name, category, unit, normal_range_min,
                    normal_range_max, cost, turnaround_hours,
                    description=""):
    """Insert a new lab test definition. Returns the inserted _id."""
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Category must be one of {VALID_CATEGORIES}")
    if normal_range_min >= normal_range_max:
        raise ValueError("normal_range_min must be less than normal_range_max")

    doc = {
        "test_name":       test_name,
        "category":        category,
        "description":     description,
        "unit":            unit,
        "normal_range_min": float(normal_range_min),
        "normal_range_max": float(normal_range_max),
        "cost":            float(cost),
        "turnaround_hours": int(turnaround_hours),
    }
    result = get_db().lab_tests.insert_one(doc)
    print(f"  ✅ Lab test '{test_name}' created (ID: {result.inserted_id})")
    return result.inserted_id


# ── READ ──────────────────────────────────────────────────────────────
def get_test_by_id(test_id):
    """Fetch a single lab test by _id."""
    doc = get_db().lab_tests.find_one({"_id": to_object_id(test_id)})
    return id_to_str(doc) if doc else None


def get_test_by_name(test_name):
    """Fetch a lab test by its unique name."""
    doc = get_db().lab_tests.find_one({"test_name": test_name})
    return id_to_str(doc) if doc else None


def get_all_tests():
    """Return all lab test definitions, sorted by category then name."""
    docs = list(get_db().lab_tests.find().sort([
        ("category", 1), ("test_name", 1)
    ]))
    return ids_to_str(docs)


def get_tests_by_category(category):
    """Return all tests in a given category."""
    docs = list(get_db().lab_tests.find({"category": category}))
    return ids_to_str(docs)


# ── UPDATE ────────────────────────────────────────────────────────────
def update_lab_test(test_id, updates: dict):
    """Update fields of a lab test document."""
    if "category" in updates and updates["category"] not in VALID_CATEGORIES:
        raise ValueError(f"Category must be one of {VALID_CATEGORIES}")
    result = get_db().lab_tests.update_one(
        {"_id": to_object_id(test_id)},
        {"$set": updates},
    )
    return result.modified_count


# ── DELETE ────────────────────────────────────────────────────────────
def delete_lab_test(test_id):
    """Delete a lab test definition."""
    result = get_db().lab_tests.delete_one({"_id": to_object_id(test_id)})
    return result.deleted_count


# ── COUNT ─────────────────────────────────────────────────────────────
def count_tests():
    return get_db().lab_tests.count_documents({})
