"""Smart MCP Client — Versioning & Metadata Resource Discovery.

Demonstrates:
1. Reading server metadata via MCP Resource (`server://info`).
2. Detecting deprecated tools, version bumps, and replacements.
3. Dynamically choosing modern v2 tools when available, with automatic fallback to v1.
4. Ensuring 100% backward compatibility for mixed-version deployments.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory for module imports
PARENT_DIR = Path(__file__).resolve().parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class SmartMCPClient:
    """Intelligent MCP Client capable of negotiating versions based on server://info."""

    def __init__(self, session: ClientSession) -> None:
        self.session = session
        self.metadata: dict[str, Any] = {}
        self.available_tools: set[str] = set()

    async def discover_capabilities(self) -> dict[str, Any]:
        """Read server://info resource and cache metadata."""
        # 1. List available tools from protocol
        tools_list = await self.session.list_tools()
        self.available_tools = {t.name for t in tools_list.tools}

        # 2. Read server metadata resource
        try:
            res = await self.session.read_resource("server://info")
            if res.contents and res.contents[0].text:
                self.metadata = json.loads(res.contents[0].text)
        except Exception as e:
            print(f"⚠️ Could not read server://info resource (Legacy server?): {e}")
            self.metadata = {}

        return self.metadata

    async def smart_search_logs(self, keyword: str) -> dict[str, Any] | str:
        """Call search_logs_v2 if supported, otherwise fallback to search_logs v1."""
        tools_meta = self.metadata.get("tools", {})
        
        # Check if v2 tool is supported and not deprecated
        if "search_logs_v2" in self.available_tools and not tools_meta.get("search_logs_v2", {}).get("deprecated", False):
            print("✨ [Smart Dispatch] Using modern 'search_logs_v2' (Structured JSON + Anomaly Detection)")
            res = await self.session.call_tool("search_logs_v2", {"keyword": keyword, "include_metrics": True})
            return json.loads(res.content[0].text)
        else:
            print("🔄 [Fallback Dispatch] Using legacy 'search_logs' (Plain Text)")
            res = await self.session.call_tool("search_logs", {"keyword": keyword})
            return res.content[0].text

    async def smart_get_order(self, order_id: str) -> dict[str, Any] | str:
        """Call get_order_v2 if supported, otherwise fallback to get_order v1."""
        if "get_order_v2" in self.available_tools:
            print("✨ [Smart Dispatch] Using modern 'get_order_v2' (Itemized JSON)")
            res = await self.session.call_tool("get_order_v2", {"order_id": order_id, "include_items": True})
            return json.loads(res.content[0].text)
        else:
            print("🔄 [Fallback Dispatch] Using legacy 'get_order' (Plain Text)")
            res = await self.session.call_tool("get_order", {"order_id": order_id})
            return res.content[0].text


async def main() -> None:
    print("=" * 70)
    print("🧠 RUNNING SMART CLIENT WITH VERSION AUTO-NEGOTIATION")
    print("=" * 70)

    server_script = PARENT_DIR / "server.py"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script), "--transport", "stdio"],
        cwd=str(PARENT_DIR),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            client = SmartMCPClient(session)

            # Step 1: Read server://info
            print("1️⃣ Reading server metadata via MCP Resource [server://info]...")
            meta = await client.discover_capabilities()
            print(f"   Server Name    : {meta.get('name')}")
            print(f"   Server Version : {meta.get('version')}")
            print(f"   Protocol       : {meta.get('protocol')}")
            print(f"   Migration Guide: {meta.get('migration_guide')}\n")

            print("   Tool Deprecation Map:")
            for t_name, t_info in meta.get("tools", {}).items():
                dep_status = "⚠️ DEPRECATED" if t_info.get("deprecated") else "✅ ACTIVE"
                rep = f"-> Replace with: {t_info.get('replacement')}" if t_info.get("replacement") else ""
                print(f"   • {t_name:<20} : {dep_status:<14} (v{t_info.get('version')}) {rep}")
            print("-" * 70)

            # Step 2: Smart call for logs
            print("2️⃣ Performing Smart Log Search for 'timeout'...")
            log_result = await client.smart_search_logs("timeout")
            print("   Output sample:")
            if isinstance(log_result, dict):
                print(f"   - API Version   : {log_result.get('api_version')}")
                print(f"   - Matches Count : {log_result.get('total_matches')}")
                print(f"   - Anomalies     : {log_result.get('anomalies_detected')}")
            else:
                print(f"   {log_result}")
            print("-" * 70)

            # Step 3: Smart call for order
            print("3️⃣ Performing Smart Order Lookup for 'ORD-2026-001'...")
            order_result = await client.smart_get_order("ORD-2026-001")
            print("   Output sample:")
            if isinstance(order_result, dict):
                print(f"   - Order ID     : {order_result.get('order_id')}")
                print(f"   - Status       : {order_result.get('status')}")
                print(f"   - Customer     : {order_result.get('customer', {}).get('name')}")
                print(f"   - Total Amount : {order_result.get('total_amount')} {order_result.get('currency')}")
                print(f"   - Items Count  : {order_result.get('item_count')}")
            else:
                print(f"   {order_result}")
            print("=" * 70)
            print("🎉 Smart Client version negotiation completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
