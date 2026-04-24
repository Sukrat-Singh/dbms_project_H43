"""
mongo_connection.py  –  MongoDB Atlas connection manager + schema validators.

Equivalent SQL concepts:
    • CREATE TABLE … (columns, types)  →  JSON Schema Validators
    • CREATE INDEX …                   →  pymongo create_index()
    • UNIQUE constraints               →  unique=True on index
"""

import os
from pymongo import MongoClient, ASCENDING
from pymongo.errors import CollectionInvalid
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

_client = None


# ══════════════════════════════════════════════════════════════════════
#  CONNECTION
# ══════════════════════════════════════════════════════════════════════
def get_client():
    global _client
    if _client is None:
        mongo_uri = st.secrets.get("MONGODB_URI")  # ✅ FIX
        if not mongo_uri:
            raise RuntimeError("MONGODB_URI not set in Streamlit secrets")
        _client = MongoClient(mongo_uri)
    return _client


def get_db():
    """Return the project database handle."""
    db_name = st.secrets.get("MONGO_DB_NAME", "lab_test_management")
    return get_client()[db_name]


# ══════════════════════════════════════════════════════════════════════
#  JSON SCHEMA VALIDATORS  (equivalent to CREATE TABLE column defs)
# ══════════════════════════════════════════════════════════════════════
PATIENT_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "age", "gender", "contact", "created_at"],
        "properties": {
            "name":       {"bsonType": "string", "description": "Patient full name"},
            "age":        {"bsonType": "int",    "minimum": 0, "maximum": 150,
                           "description": "Patient age in years"},
            "gender":     {"bsonType": "string", "enum": ["Male", "Female", "Other"]},
            "contact":    {"bsonType": "string", "description": "Phone number"},
            "email":      {"bsonType": "string", "description": "Email address"},
            "address":    {"bsonType": "string"},
            "medical_history": {"bsonType": "array",
                                "items": {"bsonType": "string"},
                                "description": "List of past conditions"},
            "created_at": {"bsonType": "date"},
        },
    }
}

LAB_TEST_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["test_name", "category", "unit", "normal_range_min",
                      "normal_range_max", "cost", "turnaround_hours"],
        "properties": {
            "test_name":       {"bsonType": "string"},
            "category":        {"bsonType": "string",
                                "enum": ["Hematology", "Biochemistry",
                                         "Microbiology", "Immunology",
                                         "Pathology", "Radiology"]},
            "description":     {"bsonType": "string"},
            "unit":            {"bsonType": "string",
                                "description": "e.g. mg/dL, g/dL, cells/μL"},
            "normal_range_min": {"bsonType": "double"},
            "normal_range_max": {"bsonType": "double"},
            "cost":            {"bsonType": "double", "minimum": 0},
            "turnaround_hours": {"bsonType": "int", "minimum": 1,
                                 "description": "Expected TAT in hours"},
        },
    }
}

LAB_ORDER_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["patient_id", "test_id", "status", "priority", "ordered_at"],
        "properties": {
            "patient_id":   {"bsonType": "objectId"},
            "test_id":      {"bsonType": "objectId"},
            "status":       {"bsonType": "string",
                             "enum": ["Pending", "Sample Collected",
                                      "Processing", "Completed", "Cancelled"]},
            "priority":     {"bsonType": "string",
                             "enum": ["Routine", "Urgent", "Critical"]},
            "result_value":  {"bsonType": ["double", "null"]},
            "ordered_at":   {"bsonType": "date"},
            "completed_at": {"bsonType": ["date", "null"]},
            "notes":        {"bsonType": "string"},
        },
    }
}

ALERT_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["order_id", "alert_type", "severity", "message", "created_at", "resolved"],
        "properties": {
            "order_id":   {"bsonType": "objectId"},
            "alert_type": {"bsonType": "string",
                           "enum": ["Critical Result", "Delayed Order",
                                    "Abnormal Result"]},
            "severity":   {"bsonType": "string",
                           "enum": ["Low", "Medium", "High", "Critical"]},
            "message":    {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
            "resolved":   {"bsonType": "bool"},
            "resolved_at": {"bsonType": ["date", "null"]},
        },
    }
}


# ══════════════════════════════════════════════════════════════════════
#  COLLECTION + INDEX SETUP  (run once on first deploy)
# ══════════════════════════════════════════════════════════════════════
def _create_or_update(db, name, validator):
    """Create a collection with a validator, or update the validator if it exists."""
    if name not in db.list_collection_names():
        db.create_collection(name, validator=validator)
        print(f"  ✅  Created collection '{name}' with schema validator")
    else:
        db.command("collMod", name, validator=validator)
        print(f"  🔄  Updated validator for existing collection '{name}'")


def setup_collections():
    """Idempotent: create collections, apply validators, build indexes."""
    db = get_db()
    print("─── Setting up collections ───")

    # 1. Patients
    _create_or_update(db, "patients", PATIENT_VALIDATOR)
    db.patients.create_index([("name", ASCENDING)])
    db.patients.create_index([("contact", ASCENDING)], unique=True)

    # 2. Lab Tests
    _create_or_update(db, "lab_tests", LAB_TEST_VALIDATOR)
    db.lab_tests.create_index([("test_name", ASCENDING)], unique=True)
    db.lab_tests.create_index([("category", ASCENDING)])

    # 3. Lab Orders
    _create_or_update(db, "lab_orders", LAB_ORDER_VALIDATOR)
    db.lab_orders.create_index([("patient_id", ASCENDING)])
    db.lab_orders.create_index([("test_id", ASCENDING)])
    db.lab_orders.create_index([("status", ASCENDING)])
    db.lab_orders.create_index([("ordered_at", ASCENDING)])

    # 4. Alerts
    _create_or_update(db, "alerts", ALERT_VALIDATOR)
    db.alerts.create_index([("order_id", ASCENDING)])
    db.alerts.create_index([("resolved", ASCENDING)])

    print("─── All collections ready ───\n")


if __name__ == "__main__":
    setup_collections()