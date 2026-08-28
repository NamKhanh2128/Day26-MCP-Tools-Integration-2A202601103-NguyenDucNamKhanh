"""Stdio Client Demo for DevOps & Database Intelligence MCP Server.

Demonstrates runtime tool discovery and execution via standard input/output.
Ideal for local agents like Claude Code, Claude Desktop, and IDE plugins.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory for module imports
PARENT_DIR = Path(__file__).resolve().parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_stdio_client() -> None:
    print("=" * 70)
    print("🔌 CONNECTING TO DEVOPS MCP SERVER VIA STDIO")
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
            print("✅ MCP Session Initialized successfully!\n")

            # 1. Tool Discovery
            tools = await session.list_tools()
            print(f"📦 Discovered {len(tools.tools)} Tools from Server:")
            for t in tools.tools:
                print(f"   • {t.name:<22} : {t.description.splitlines()[0]}")
            print()

            # 2. Call Tool: search_logs (v1 legacy)
            print("▶️ Calling [search_logs (v1)] keyword='error':")
            v1_log_res = await session.call_tool("search_logs", {"keyword": "error", "limit": 2})
            print(v1_log_res.content[0].text)
            print("-" * 70)

            # 3. Call Tool: search_logs_v2 (v2 structured JSON)
            print("▶️ Calling [search_logs_v2 (v2)] keyword='timeout', include_metrics=True:")
            v2_log_res = await session.call_tool("search_logs_v2", {"keyword": "timeout", "include_metrics": True})
            parsed_v2 = json.loads(v2_log_res.content[0].text)
            print(f"   API Version    : {parsed_v2.get('api_version')}")
            print(f"   Total Matches  : {parsed_v2.get('total_matches')}")
            print(f"   Anomalies Found: {len(parsed_v2.get('anomalies_detected', []))}")
            if parsed_v2.get("remediation_recommendations"):
                print(f"   Recommendation : {parsed_v2['remediation_recommendations'][0]}")
            print("-" * 70)

            # 4. Call Tool: get_order_v2 (v2 detailed order inspection)
            print("▶️ Calling [get_order_v2 (v2)] order_id='ORD-2026-001':")
            order_res = await session.call_tool("get_order_v2", {"order_id": "ORD-2026-001", "include_items": True})
            print(json.dumps(json.loads(order_res.content[0].text), indent=2, ensure_ascii=False))
            print("-" * 70)

            # 5. Call Tool: get_database_summary
            print("▶️ Calling [get_database_summary]:")
            db_res = await session.call_tool("get_database_summary", {})
            print(json.dumps(json.loads(db_res.content[0].text), indent=2, ensure_ascii=False))
            print("-" * 70)

            # 6. Call Tool: check_system_health
            print("▶️ Calling [check_system_health]:")
            health_res = await session.call_tool("check_system_health", {})
            print(json.dumps(json.loads(health_res.content[0].text), indent=2, ensure_ascii=False))
            print("=" * 70)
            print("🎉 Stdio Client demo completed with 100% success!")


if __name__ == "__main__":
    asyncio.run(run_stdio_client())
