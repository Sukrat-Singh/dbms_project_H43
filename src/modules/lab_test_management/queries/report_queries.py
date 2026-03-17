"""
report_queries.py  –  Aggregation pipelines for generating reports.
"""

from db.mongo_connection import get_db
from utils.helpers import to_object_id


def patient_full_report(patient_id):
    """
    SQL:  SELECT p.*, o.*, t.test_name, t.unit, t.normal_range_min, t.normal_range_max
          FROM patients p
          JOIN lab_orders o ON p.id = o.patient_id
          JOIN lab_tests  t ON o.test_id = t.id
          WHERE p.id = :pid
          ORDER BY o.ordered_at DESC;
    """
    pipeline = [
        {"$match": {"_id": to_object_id(patient_id)}},
        {"$lookup": {
            "from": "lab_orders",
            "localField": "_id",
            "foreignField": "patient_id",
            "as": "orders",
        }},
        {"$unwind": {"path": "$orders", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "lab_tests",
            "localField": "orders.test_id",
            "foreignField": "_id",
            "as": "orders.test_info",
        }},
        {"$unwind": {"path": "$orders.test_info", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$_id",
            "name":    {"$first": "$name"},
            "age":     {"$first": "$age"},
            "gender":  {"$first": "$gender"},
            "contact": {"$first": "$contact"},
            "orders":  {"$push": {
                "order_id":      "$orders._id",
                "test_name":     "$orders.test_info.test_name",
                "status":        "$orders.status",
                "priority":      "$orders.priority",
                "result_value":  "$orders.result_value",
                "unit":          "$orders.test_info.unit",
                "normal_min":    "$orders.test_info.normal_range_min",
                "normal_max":    "$orders.test_info.normal_range_max",
                "ordered_at":    "$orders.ordered_at",
                "completed_at":  "$orders.completed_at",
            }},
        }},
        {"$project": {"_id": 0}},
    ]
    results = list(get_db().patients.aggregate(pipeline))
    return results[0] if results else None


def daily_orders_report(year, month, day):
    """
    SQL:  SELECT o.*, p.name AS patient_name, t.test_name
          FROM lab_orders o
          JOIN patients  p ON o.patient_id = p.id
          JOIN lab_tests t ON o.test_id    = t.id
          WHERE DATE(o.ordered_at) = ':year-:month-:day'
          ORDER BY o.ordered_at;
    """
    from datetime import datetime, timezone
    start = datetime(year, month, day, tzinfo=timezone.utc)
    end   = datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc)

    pipeline = [
        {"$match": {"ordered_at": {"$gte": start, "$lte": end}}},
        {"$lookup": {
            "from": "patients",
            "localField": "patient_id",
            "foreignField": "_id",
            "as": "patient",
        }},
        {"$unwind": "$patient"},
        {"$lookup": {
            "from": "lab_tests",
            "localField": "test_id",
            "foreignField": "_id",
            "as": "test",
        }},
        {"$unwind": "$test"},
        {"$project": {
            "_id":          0,
            "order_id":     {"$toString": "$_id"},
            "patient_name": "$patient.name",
            "test_name":    "$test.test_name",
            "status":       1,
            "priority":     1,
            "result_value": 1,
            "ordered_at":   1,
        }},
        {"$sort": {"ordered_at": 1}},
    ]
    return list(get_db().lab_orders.aggregate(pipeline))


def test_result_summary():
    """
    SQL:  SELECT t.test_name,
                 COUNT(o.id) AS total,
                 AVG(o.result_value) AS avg_result,
                 MIN(o.result_value) AS min_result,
                 MAX(o.result_value) AS max_result
          FROM lab_orders o
          JOIN lab_tests t ON o.test_id = t.id
          WHERE o.result_value IS NOT NULL
          GROUP BY t.test_name;
    """
    pipeline = [
        {"$match": {"result_value": {"$ne": None}}},
        {"$lookup": {
            "from": "lab_tests",
            "localField": "test_id",
            "foreignField": "_id",
            "as": "test",
        }},
        {"$unwind": "$test"},
        {"$group": {
            "_id":        "$test.test_name",
            "total":      {"$sum": 1},
            "avg_result": {"$avg": "$result_value"},
            "min_result": {"$min": "$result_value"},
            "max_result": {"$max": "$result_value"},
            "unit":       {"$first": "$test.unit"},
            "normal_min": {"$first": "$test.normal_range_min"},
            "normal_max": {"$first": "$test.normal_range_max"},
        }},
        {"$project": {
            "_id": 0,
            "test_name":  "$_id",
            "total":      1,
            "avg_result": {"$round": ["$avg_result", 2]},
            "min_result": 1,
            "max_result": 1,
            "unit":       1,
            "normal_min": 1,
            "normal_max": 1,
        }},
        {"$sort": {"test_name": 1}},
    ]
    return list(get_db().lab_orders.aggregate(pipeline))
