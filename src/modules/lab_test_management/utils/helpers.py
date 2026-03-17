"""
helpers.py  –  Utility functions used across the Lab Test Management System.
"""

from datetime import datetime, timezone
from bson import ObjectId


# ── ObjectId helpers ──────────────────────────────────────────────────
def to_object_id(id_value):
    """Convert a string to a BSON ObjectId; return as-is if already one."""
    if isinstance(id_value, ObjectId):
        return id_value
    return ObjectId(id_value)


def id_to_str(doc):
    """Convert the '_id' field of a MongoDB document to a string for display."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def ids_to_str(docs):
    """Convert '_id' in every document of a list."""
    return [id_to_str(d) for d in docs]


# ── Date / Time helpers ──────────────────────────────────────────────
def now_utc():
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def format_datetime(dt, fmt="%Y-%m-%d %H:%M:%S"):
    """Format a datetime object to a readable string."""
    if dt is None:
        return "N/A"
    return dt.strftime(fmt)


def hours_between(start, end):
    """Return the number of hours between two datetimes."""
    if start is None or end is None:
        return None
    delta = end - start
    return round(delta.total_seconds() / 3600, 2)


# ── Display helpers ───────────────────────────────────────────────────
def format_currency(amount):
    """Format a number as Indian Rupee currency string."""
    return f"₹{amount:,.2f}"


def truncate(text, length=50):
    """Truncate text with ellipsis if longer than *length*."""
    if text and len(text) > length:
        return text[:length - 3] + "..."
    return text
