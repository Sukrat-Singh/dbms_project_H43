"""
patient_model.py  –  Patient collection schema & CRUD operations.

SQL equivalent:
    CREATE TABLE patients (
        id          SERIAL PRIMARY KEY,
        name        VARCHAR(100) NOT NULL,
        age         INT CHECK (age >= 0 AND age <= 150),
        gender      ENUM('Male','Female','Other'),
        contact     VARCHAR(15) UNIQUE NOT NULL,
        email       VARCHAR(100),
        address     TEXT,
        medical_history TEXT[],
        created_at  TIMESTAMP DEFAULT NOW()
    );
"""

from db.mongo_connection import get_db
from utils.helpers import to_object_id, id_to_str, ids_to_str, now_utc
from utils.constants import VALID_GENDERS


# ── CREATE ────────────────────────────────────────────────────────────
def create_patient(name, age, gender, contact, email="", address="",
                   medical_history=None):
    """Insert a new patient document. Returns the inserted _id."""
    if gender not in VALID_GENDERS:
        raise ValueError(f"Gender must be one of {VALID_GENDERS}")
    if age < 0 or age > 150:
        raise ValueError("Age must be between 0 and 150")

    doc = {
        "name":    name,
        "age":     int(age),
        "gender":  gender,
        "contact": contact,
        "email":   email,
        "address": address,
        "medical_history": medical_history or [],
        "created_at": now_utc(),
    }
    result = get_db().patients.insert_one(doc)
    print(f"  ✅ Patient '{name}' created (ID: {result.inserted_id})")
    return result.inserted_id


# ── READ ──────────────────────────────────────────────────────────────
def get_patient_by_id(patient_id):
    """Fetch a single patient by _id."""
    doc = get_db().patients.find_one({"_id": to_object_id(patient_id)})
    return id_to_str(doc) if doc else None


def get_all_patients():
    """Return all patients, sorted by name."""
    docs = list(get_db().patients.find().sort("name", 1))
    return ids_to_str(docs)


def search_patients(keyword):
    """Case-insensitive search on patient name."""
    regex = {"$regex": keyword, "$options": "i"}
    docs = list(get_db().patients.find({"name": regex}))
    return ids_to_str(docs)


# ── UPDATE ────────────────────────────────────────────────────────────
def update_patient(patient_id, updates: dict):
    """Update specific fields of a patient document."""
    if "gender" in updates and updates["gender"] not in VALID_GENDERS:
        raise ValueError(f"Gender must be one of {VALID_GENDERS}")
    result = get_db().patients.update_one(
        {"_id": to_object_id(patient_id)},
        {"$set": updates},
    )
    return result.modified_count


# ── DELETE ────────────────────────────────────────────────────────────
def delete_patient(patient_id):
    """Delete a patient by _id."""
    result = get_db().patients.delete_one({"_id": to_object_id(patient_id)})
    return result.deleted_count


# ── COUNT ─────────────────────────────────────────────────────────────
def count_patients():
    """Return the total number of patients."""
    return get_db().patients.count_documents({})
