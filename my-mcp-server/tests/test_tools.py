"""Unit tests for DevOps MCP Server Tools."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
import sys

# Ensure parent directory is in sys.path
PARENT_DIR = Path(__file__).resolve().parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from tools import database as db_tools
from tools import logs as log_tools
from tools import system as sys_tools


class TestLogTools(unittest.TestCase):
    """Test log analysis and anomaly detection tools."""

    def test_search_logs_v1(self) -> None:
        """Test legacy search_logs tool returns formatted string."""
        res = log_tools.search_logs(keyword="error", limit=5)
        self.assertIsInstance(res, str)
        self.assertIn("Results", res)
        self.assertIn("ERROR", res)

    def test_search_logs_v2_structured(self) -> None:
        """Test modern search_logs_v2 returns valid structured JSON."""
        res_str = log_tools.search_logs_v2(keyword="timeout", include_metrics=True)
        data = json.loads(res_str)
        self.assertEqual(data.get("api_version"), "2.1.0")
        self.assertIn("results", data)
        self.assertIn("metrics", data)
        self.assertIn("anomalies_detected", data)
        self.assertIn("remediation_recommendations", data)
        self.assertGreaterEqual(data.get("total_matches", 0), 1)

    def test_get_recent_errors(self) -> None:
        """Test get_recent_errors extracts ERROR and CRITICAL entries."""
        res_str = log_tools.get_recent_errors(limit=5, include_stacktrace=True)
        data = json.loads(res_str)
        self.assertEqual(data.get("api_version"), "2.1.0")
        self.assertIn("errors", data)
        self.assertGreaterEqual(data.get("error_count", 0), 1)

    def test_get_log_summary(self) -> None:
        """Test get_log_summary aggregates active modules and levels."""
        res_str = log_tools.get_log_summary()
        data = json.loads(res_str)
        self.assertEqual(data.get("api_version"), "2.1.0")
        self.assertIn("levels", data)
        self.assertIn("top_active_modules", data)
        self.assertGreater(data.get("total_records", 0), 0)


class TestDatabaseTools(unittest.TestCase):
    """Test database inspection and order tools."""

    def test_get_order_v1_legacy(self) -> None:
        """Test legacy get_order returns plain string."""
        res = db_tools.get_order("ORD-2026-001")
        self.assertIsInstance(res, str)
        self.assertIn("ORD-2026-001", res)
        self.assertIn("COMPLETED", res)

    def test_get_order_v2_structured(self) -> None:
        """Test modern get_order_v2 returns full JSON itemization."""
        res_str = db_tools.get_order_v2("ORD-2026-001", include_items=True, include_customer=True)
        data = json.loads(res_str)
        self.assertEqual(data.get("api_version"), "2.1.0")
        self.assertEqual(data.get("order_id"), "ORD-2026-001")
        self.assertEqual(data.get("status"), "COMPLETED")
        self.assertIn("customer", data)
        self.assertIn("items", data)
        self.assertGreater(data.get("item_count", 0), 0)

    def test_search_orders(self) -> None:
        """Test search_orders filters by status and min amount."""
        res_str = db_tools.search_orders(status="COMPLETED", min_amount=100.0)
        data = json.loads(res_str)
        self.assertEqual(data.get("api_version"), "2.1.0")
        self.assertIn("orders", data)
        for order in data["orders"]:
            self.assertEqual(order["status"], "COMPLETED")
            self.assertGreaterEqual(order["total_amount"], 100.0)

    def test_get_database_summary(self) -> None:
        """Test get_database_summary calculates revenue and tables metrics."""
        res_str = db_tools.get_database_summary()
        data = json.loads(res_str)
        self.assertEqual(data.get("api_version"), "2.1.0")
        self.assertIn("tables", data)
        self.assertIn("business_analytics", data)
        self.assertGreater(data["business_analytics"]["total_completed_revenue_usd"], 0)


class TestSystemTools(unittest.TestCase):
    """Test system health and telemetry tools."""

    def test_check_system_health(self) -> None:
        """Test check_system_health returns valid system status."""
        res_str = sys_tools.check_system_health()
        data = json.loads(res_str)
        self.assertEqual(data.get("api_version"), "2.1.0")
        self.assertEqual(data.get("status"), "HEALTHY")
        self.assertIn("host", data)
        self.assertIn("resources", data)
        self.assertIn("dependencies", data)


if __name__ == "__main__":
    unittest.main()
