"""Unit tests for Server Versioning and Resource Metadata."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Ensure parent directory is in sys.path
PARENT_DIR = Path(__file__).resolve().parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from server import server_info


class TestServerVersioning(unittest.TestCase):
    """Test server://info metadata resource and deprecation mappings."""

    def test_server_info_schema(self) -> None:
        """Verify server_info returns valid metadata with required fields."""
        raw_info = server_info()
        self.assertIsInstance(raw_info, str)

        info = json.loads(raw_info)
        self.assertEqual(info.get("name"), "devops-mcp-server")
        self.assertEqual(info.get("version"), "2.1.0")
        self.assertIn("tools", info)
        self.assertIn("capabilities", info)
        self.assertIn("migration_guide", info)

    def test_deprecation_mappings(self) -> None:
        """Verify v1 tools are marked deprecated and have replacements."""
        info = json.loads(server_info())
        tools = info["tools"]

        # search_logs should be deprecated and point to search_logs_v2
        self.assertTrue(tools["search_logs"]["deprecated"])
        self.assertEqual(tools["search_logs"]["replacement"], "search_logs_v2")

        # get_order should be deprecated and point to get_order_v2
        self.assertTrue(tools["get_order"]["deprecated"])
        self.assertEqual(tools["get_order"]["replacement"], "get_order_v2")

        # v2 tools should NOT be deprecated
        self.assertFalse(tools["search_logs_v2"]["deprecated"])
        self.assertFalse(tools["get_order_v2"]["deprecated"])


if __name__ == "__main__":
    unittest.main()
