"""
analytics_queries.py  –  Aggregation pipelines for analytics.

Each function documents the equivalent SQL query it replaces.
"""

from db.mongo_connection import get_db


def tests_per_category():
    """
    SQL:  SELECT category, COUNT(*) AS total
          FROM lab_tests GROUP BY category ORDER BY total DESC;
    """
    pipeline = [
        {"$group": {"_id": "$category", "total": {"$sum": 1}}},
        {"$project": {"_id": 0, "category": "$_id", "total": 1}},
        {"$sort": {"total": -1}},
    ]
    return list(get_db().lab_tests.aggregate(pipeline))


def orders_by_status():
    """
    SQL:  SELECT status, COUNT(*) AS total
          FROM lab_orders GROUP BY status;
    """
    pipeline = [
        {"$group": {"_id": "$status", "total": {"$sum": 1}}},
        {"$project": {"_id": 0, "status": "$_id", "total": 1}},
        {"$sort": {"total": -1}},
    ]
    return list(get_db().lab_orders.aggregate(pipeline))


def orders_by_priority():
    """
    SQL:  SELECT priority, COUNT(*) AS total
          FROM lab_orders GROUP BY priority;
    """
    pipeline = [
        {"$group": {"_id": "$priority", "total": {"$sum": 1}}},
        {"$project": {"_id": 0, "priority": "$_id", "total": 1}},
        {"$sort": {"total": -1}},
    ]
    return list(get_db().lab_orders.aggregate(pipeline))


def revenue_by_test():
    """
    SQL:  SELECT t.test_name, t.cost, COUNT(o.id) AS order_count,
                 SUM(t.cost) AS total_revenue
          FROM lab_orders o
          JOIN lab_tests t ON o.test_id = t.id
          WHERE o.status = 'Completed'
          GROUP BY t.test_name, t.cost
          ORDER BY total_revenue DESC;
    """
    pipeline = [
        {"$match": {"status": "Completed"}},
        {"$lookup": {
            "from": "lab_tests",
            "localField": "test_id",
            "foreignField": "_id",
            "as": "test",
        }},
        {"$unwind": "$test"},
        {"$group": {
            "_id": "$test.test_name",
            "cost_per_test": {"$first": "$test.cost"},
            "order_count":   {"$sum": 1},
            "total_revenue": {"$sum": "$test.cost"},
        }},
        {"$project": {
            "_id": 0,
            "test_name":     "$_id",
            "cost_per_test": 1,
            "order_count":   1,
            "total_revenue": {"$round": ["$total_revenue", 2]},
        }},
        {"$sort": {"total_revenue": -1}},
    ]
    return list(get_db().lab_orders.aggregate(pipeline))


def monthly_order_trends():
    """
    SQL:  SELECT DATE_FORMAT(ordered_at, '%Y-%m') AS month,
                 COUNT(*) AS total_orders
          FROM lab_orders
          GROUP BY month ORDER BY month;
    """
    pipeline = [
        {"$group": {
            "_id": {
                "year":  {"$year": "$ordered_at"},
                "month": {"$month": "$ordered_at"},
            },
            "total_orders": {"$sum": 1},
        }},
        {"$project": {
            "_id": 0,
            "month": {
                "$concat": [
                    {"$toString": "$_id.year"}, "-",
                    {"$cond": [
                        {"$lt": ["$_id.month", 10]},
                        {"$concat": ["0", {"$toString": "$_id.month"}]},
                        {"$toString": "$_id.month"},
                    ]},
                ]
            },
            "total_orders": 1,
        }},
        {"$sort": {"month": 1}},
    ]
    return list(get_db().lab_orders.aggregate(pipeline))


def patient_order_summary():
    """
    SQL:  SELECT p.name, COUNT(o.id) AS total_orders,
                 SUM(CASE WHEN o.status='Completed' THEN 1 ELSE 0 END) AS completed
          FROM patients p
          LEFT JOIN lab_orders o ON p.id = o.patient_id
          GROUP BY p.name
          ORDER BY total_orders DESC;
    """
    pipeline = [
        {"$lookup": {
            "from": "lab_orders",
            "localField": "_id",
            "foreignField": "patient_id",
            "as": "orders",
        }},
        {"$project": {
            "_id": 0,
            "patient_name": "$name",
            "total_orders": {"$size": "$orders"},
            "completed": {
                "$size": {
                    "$filter": {
                        "input": "$orders",
                        "as": "o",
                        "cond": {"$eq": ["$$o.status", "Completed"]},
                    }
                }
            },
        }},
        {"$sort": {"total_orders": -1}},
    ]
    return list(get_db().patients.aggregate(pipeline))
