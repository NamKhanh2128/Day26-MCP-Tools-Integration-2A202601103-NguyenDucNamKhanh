"""Database Intelligence & Order Inspection Tools.

Provides query, inspection, and business metrics capabilities.
Supports versioning with backward compatibility:
- get_order: v1 legacy tool (returns concise text).
- get_order_v2: v2 enhanced tool (returns full JSON object with item breakdown and tracking).
- search_orders: Filter orders by status and price thresholds.
- get_database_summary: High-level database schema and transaction analytics.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from config import ORDERS_JSON_PATH, SQLITE_DB_PATH, DATA_DIR


def _init_sqlite_db() -> None:
    """Initialize local SQLite database seeded from sample_orders.json if not present."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_name TEXT,
        customer_email TEXT,
        customer_phone TEXT,
        total_amount REAL,
        currency TEXT,
        status TEXT,
        payment_method TEXT,
        tracking_number TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        sku TEXT,
        name TEXT,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
    """)

    # Seed data if empty
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    if count == 0 and ORDERS_JSON_PATH.exists():
        with open(ORDERS_JSON_PATH, "r", encoding="utf-8") as f:
            orders = json.load(f)
            for o in orders:
                cust = o.get("customer", {})
                cursor.execute("""
                INSERT INTO orders (order_id, customer_name, customer_email, customer_phone, total_amount, currency, status, payment_method, tracking_number, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    o["order_id"],
                    cust.get("name", "Unknown"),
                    cust.get("email", ""),
                    cust.get("phone", ""),
                    o.get("total_amount", 0.0),
                    o.get("currency", "USD"),
                    o.get("status", "PENDING"),
                    o.get("payment_method", ""),
                    o.get("tracking_number"),
                    o.get("created_at", ""),
                    o.get("updated_at", ""),
                ))
                for item in o.get("items", []):
                    cursor.execute("""
                    INSERT INTO order_items (order_id, sku, name, quantity, price)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        o["order_id"],
                        item.get("sku", ""),
                        item.get("name", ""),
                        item.get("quantity", 1),
                        item.get("price", 0.0),
                    ))
        conn.commit()

    conn.close()


def _get_orders_from_source() -> list[dict[str, Any]]:
    """Helper to load orders from SQLite or fallback to JSON."""
    _init_sqlite_db()
    if SQLITE_DB_PATH.exists():
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders")
        rows = cursor.fetchall()
        orders = []
        for r in rows:
            order_id = r["order_id"]
            cursor.execute("SELECT sku, name, quantity, price FROM order_items WHERE order_id = ?", (order_id,))
            item_rows = cursor.fetchall()
            items = [{"sku": i["sku"], "name": i["name"], "quantity": i["quantity"], "price": i["price"]} for i in item_rows]
            orders.append({
                "order_id": r["order_id"],
                "customer": {
                    "name": r["customer_name"],
                    "email": r["customer_email"],
                    "phone": r["customer_phone"],
                },
                "total_amount": r["total_amount"],
                "currency": r["currency"],
                "status": r["status"],
                "payment_method": r["payment_method"],
                "tracking_number": r["tracking_number"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "items": items,
            })
        conn.close()
        return orders

    if ORDERS_JSON_PATH.exists():
        with open(ORDERS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    return []


# ── Tool v1: get_order (Legacy Text Response) ────────────────────────
def get_order(order_id: str) -> str:
    """[v1] Lookup customer order by order_id.
    
    Returns concise text line for legacy MCP clients.
    Deprecated: Prefer get_order_v2 for comprehensive JSON schema with itemized breakdown.

    Args:
        order_id: Order identifier (e.g., "ORD-2026-001", "ORD-2026-003").
    """
    orders = _get_orders_from_source()
    for o in orders:
        if o["order_id"].upper() == order_id.strip().upper():
            cust_name = o.get("customer", {}).get("name", "Unknown")
            return f"Order {o['order_id']}: Status={o['status']}, Total={o['total_amount']} {o['currency']}, Customer={cust_name}"

    return f"Order '{order_id}' not found in database."


# ── Tool v2: get_order_v2 (Rich Structured JSON Response) ────────────
def get_order_v2(
    order_id: str,
    include_items: bool = True,
    include_customer: bool = True,
) -> str:
    """[v2] Detailed order inspection with full itemization and fulfillment status.

    Args:
        order_id: Order identifier (e.g., "ORD-2026-001").
        include_items: Whether to include itemized line products (default True).
        include_customer: Whether to include customer contact details (default True).
    """
    orders = _get_orders_from_source()
    for o in orders:
        if o["order_id"].upper() == order_id.strip().upper():
            result: dict[str, Any] = {
                "api_version": "2.1.0",
                "order_id": o["order_id"],
                "status": o["status"],
                "total_amount": o["total_amount"],
                "currency": o["currency"],
                "payment_method": o.get("payment_method"),
                "tracking_number": o.get("tracking_number"),
                "created_at": o.get("created_at"),
                "updated_at": o.get("updated_at"),
            }
            if include_customer:
                result["customer"] = o.get("customer", {})
            if include_items:
                result["items"] = o.get("items", [])
                result["item_count"] = sum(i.get("quantity", 1) for i in o.get("items", []))

            return json.dumps(result, indent=2, ensure_ascii=False)

    return json.dumps({
        "api_version": "2.1.0",
        "error": "NOT_FOUND",
        "message": f"Order with ID '{order_id}' does not exist in database.",
    }, indent=2)


# ── Tool: search_orders ──────────────────────────────────────────────
def search_orders(
    status: str = "ALL",
    min_amount: float = 0.0,
    limit: int = 20,
) -> str:
    """Search and filter orders by payment/fulfillment status and minimum spend.

    Args:
        status: Filter by status: "ALL", "COMPLETED", "PROCESSING", "PENDING_PAYMENT", "CANCELLED".
        min_amount: Minimum order value threshold (default 0.0).
        limit: Maximum number of orders to return (default 20).
    """
    orders = _get_orders_from_source()
    filtered = []
    status_filter = status.upper()

    for o in orders:
        if status_filter != "ALL" and o["status"].upper() != status_filter:
            continue
        if float(o.get("total_amount", 0.0)) < min_amount:
            continue
        filtered.append({
            "order_id": o["order_id"],
            "customer_name": o.get("customer", {}).get("name", "Unknown"),
            "status": o["status"],
            "total_amount": o["total_amount"],
            "currency": o["currency"],
            "created_at": o.get("created_at"),
        })
        if len(filtered) >= limit:
            break

    payload = {
        "api_version": "2.1.0",
        "filter": {"status": status, "min_amount": min_amount, "limit": limit},
        "count": len(filtered),
        "orders": filtered,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ── Tool: get_database_summary ───────────────────────────────────────
def get_database_summary() -> str:
    """Return database schema metrics, active tables, row counts, and sales summaries."""
    orders = _get_orders_from_source()
    status_counts: dict[str, int] = {}
    total_revenue = 0.0

    for o in orders:
        st = o["status"]
        status_counts[st] = status_counts.get(st, 0) + 1
        if st in ("COMPLETED", "PROCESSING"):
            total_revenue += float(o.get("total_amount", 0.0))

    summary = {
        "api_version": "2.1.0",
        "database_type": "SQLite / PostgreSQL Hybrid Gateway",
        "tables": [
            {"table_name": "orders", "description": "Primary orders table", "estimated_rows": len(orders)},
            {"table_name": "order_items", "description": "Order line item SKUs", "estimated_rows": sum(len(o.get("items", [])) for o in orders)},
        ],
        "business_analytics": {
            "total_orders": len(orders),
            "status_breakdown": status_counts,
            "total_completed_revenue_usd": round(total_revenue, 2),
            "average_order_value_usd": round(total_revenue / max(status_counts.get("COMPLETED", 1), 1), 2),
        },
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)
