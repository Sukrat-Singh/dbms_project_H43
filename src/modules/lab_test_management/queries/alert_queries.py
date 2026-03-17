"""
alert_queries.py  –  Aggregation pipelines for alert analytics.
"""

from db.mongo_connection import get_db


def alerts_by_severity():
    """
    SQL:  SELECT severity, COUNT(*) AS total
          FROM alerts GROUP BY severity ORDER BY total DESC;
    """
    pipeline = [
        {"$group": {"_id": "$severity", "total": {"$sum": 1}}},
        {"$project": {"_id": 0, "severity": "$_id", "total": 1}},
        {"$sort": {"total": -1}},
    ]
    return list(get_db().alerts.aggregate(pipeline))


def alerts_by_type():
    """
    SQL:  SELECT alert_type, COUNT(*) AS total
          FROM alerts GROUP BY alert_type;
    """
    pipeline = [
        {"$group": {"_id": "$alert_type", "total": {"$sum": 1}}},
        {"$project": {"_id": 0, "alert_type": "$_id", "total": 1}},
        {"$sort": {"total": -1}},
    ]
    return list(get_db().alerts.aggregate(pipeline))


def unresolved_critical_alerts():
    """
    SQL:  SELECT a.*, o.patient_id, t.test_name
          FROM alerts a
          JOIN lab_orders o ON a.order_id = o.id
          JOIN lab_tests  t ON o.test_id  = t.id
          WHERE a.resolved = FALSE AND a.severity = 'Critical'
          ORDER BY a.created_at DESC;
    """
    pipeline = [
        {"$match": {"resolved": False, "severity": "Critical"}},
        {"$lookup": {
            "from": "lab_orders",
            "localField": "order_id",
            "foreignField": "_id",
            "as": "order",
        }},
        {"$unwind": "$order"},
        {"$lookup": {
            "from": "lab_tests",
            "localField": "order.test_id",
            "foreignField": "_id",
            "as": "test",
        }},
        {"$unwind": "$test"},
        {"$project": {
            "_id":        0,
            "alert_id":   {"$toString": "$_id"},
            "alert_type": 1,
            "severity":   1,
            "message":    1,
            "created_at": 1,
            "test_name":  "$test.test_name",
            "patient_id": {"$toString": "$order.patient_id"},
        }},
        {"$sort": {"created_at": -1}},
    ]
    return list(get_db().alerts.aggregate(pipeline))


def alert_resolution_rate():
    """
    SQL:  SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN resolved THEN 1 ELSE 0 END) AS resolved_count,
            ROUND(SUM(CASE WHEN resolved THEN 1 ELSE 0 END)*100.0/COUNT(*), 2) AS rate
          FROM alerts;
    """
    pipeline = [
        {"$group": {
            "_id": None,
            "total":    {"$sum": 1},
            "resolved": {"$sum": {"$cond": ["$resolved", 1, 0]}},
        }},
        {"$project": {
            "_id": 0,
            "total_alerts":    "$total",
            "resolved_alerts": "$resolved",
            "resolution_rate": {
                "$round": [
                    {"$multiply": [
                        {"$divide": ["$resolved", "$total"]}, 100
                    ]}, 2
                ]
            },
        }},
    ]
    result = list(get_db().alerts.aggregate(pipeline))
    return result[0] if result else {"total_alerts": 0, "resolved_alerts": 0, "resolution_rate": 0}
