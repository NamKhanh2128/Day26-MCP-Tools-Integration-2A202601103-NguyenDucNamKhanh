"""DevOps & Database Intelligence MCP Server.

Supports:
1. stdio transport for local Claude Code / Claude Desktop / Cursor integration.
2. Streamable HTTP transport with Bearer TokenVerifier for remote / production deployment.
3. Tool Versioning & Backward Compatibility (v1 text output + v2 structured JSON).
4. Metadata Resource `server://info` for runtime client capability discovery.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add current dir to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

from config import (
    DEFAULT_AUTH_TOKEN,
    HOST,
    PORT,
    PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    VALID_TOKENS,
)
from tools import database as db_tools
from tools import logs as log_tools
from tools import system as sys_tools


# ── 1. Authentication: Bearer TokenVerifier ───────────────────────────
class DevOpsTokenVerifier(TokenVerifier):
    """Verifies Bearer access tokens for Streamable HTTP requests."""

    async def verify_token(self, token: str) -> AccessToken | None:
        token_data = VALID_TOKENS.get(token)
        if token_data is None:
            return None
        return AccessToken(
            token=token,
            client_id=str(token_data["client_id"]),
            scopes=list(token_data["scopes"]),
        )


# ── 2. MCP Server Instance ───────────────────────────────────────────
mcp = MCPServer(
    SERVER_NAME,
    instructions=(
        f"{SERVER_NAME} v{SERVER_VERSION} ({PROTOCOL_VERSION}). "
        "Provides DevOps Log Diagnostics, Database Intelligence, and System Telemetry tools."
    ),
    auth=AuthSettings(
        issuer_url=f"http://localhost:{PORT}",
        resource_server_url=f"http://localhost:{PORT}",
    ),
    token_verifier=DevOpsTokenVerifier(),
)


# ── 3. Registered Tools (v1 Legacy + v2 Modern + Core Utilities) ───────
@mcp.tool()
def search_logs(keyword: str = "", level: str = "ALL", limit: int = 50) -> str:
    """[v1] Search application logs by keyword and level (plain text). Deprecated: use search_logs_v2."""
    return log_tools.search_logs(keyword=keyword, level=level, limit=limit)


@mcp.tool()
def search_logs_v2(
    keyword: str = "",
    level: str = "ALL",
    limit: int = 50,
    include_metrics: bool = True,
) -> str:
    """[v2] Advanced search and diagnostic analysis on application logs with anomaly detection."""
    return log_tools.search_logs_v2(
        keyword=keyword,
        level=level,
        limit=limit,
        include_metrics=include_metrics,
    )


@mcp.tool()
def get_recent_errors(limit: int = 10, include_stacktrace: bool = True) -> str:
    """Extract and diagnose the most recent ERROR and CRITICAL system issues."""
    return log_tools.get_recent_errors(limit=limit, include_stacktrace=include_stacktrace)


@mcp.tool()
def get_log_summary() -> str:
    """Return high-level summary metrics and module activity of application logs."""
    return log_tools.get_log_summary()


@mcp.tool()
def get_order(order_id: str) -> str:
    """[v1] Lookup customer order by ID (plain text). Deprecated: use get_order_v2."""
    return db_tools.get_order(order_id=order_id)


@mcp.tool()
def get_order_v2(
    order_id: str,
    include_items: bool = True,
    include_customer: bool = True,
) -> str:
    """[v2] Detailed order inspection with itemization and delivery tracking in JSON."""
    return db_tools.get_order_v2(
        order_id=order_id,
        include_items=include_items,
        include_customer=include_customer,
    )


@mcp.tool()
def search_orders(
    status: str = "ALL",
    min_amount: float = 0.0,
    limit: int = 20,
) -> str:
    """Search and filter orders by status and minimum transaction amount."""
    return db_tools.search_orders(status=status, min_amount=min_amount, limit=limit)


@mcp.tool()
def get_database_summary() -> str:
    """Return database schema metrics, active tables, row counts, and revenue analytics."""
    return db_tools.get_database_summary()


@mcp.tool()
def check_system_health() -> str:
    """Check host machine CPU, memory, disk, process uptime, and storage health."""
    return sys_tools.check_system_health()


# ── 4. Metadata Resource: server://info ────────────────────────────────
@mcp.resource("server://info")
def server_info() -> str:
    """Return server metadata, tool versions, deprecations, and capability guides."""
    info_payload = {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocol": PROTOCOL_VERSION,
        "capabilities": {
            "tools": True,
            "resources": True,
            "authentication": "Bearer TokenVerifier (Streamable HTTP)",
            "transports": ["stdio", "streamable-http"],
        },
        "tools": {
            "search_logs": {
                "version": "1.0.0",
                "deprecated": True,
                "replacement": "search_logs_v2",
                "format": "text",
            },
            "search_logs_v2": {
                "version": "2.1.0",
                "deprecated": False,
                "format": "json",
                "features": ["metrics", "anomaly_detection", "remediation"],
            },
            "get_recent_errors": {
                "version": "2.0.0",
                "deprecated": False,
                "format": "json",
            },
            "get_log_summary": {
                "version": "2.0.0",
                "deprecated": False,
                "format": "json",
            },
            "get_order": {
                "version": "1.0.0",
                "deprecated": True,
                "replacement": "get_order_v2",
                "format": "text",
            },
            "get_order_v2": {
                "version": "2.1.0",
                "deprecated": False,
                "format": "json",
                "features": ["itemization", "customer_details", "tracking"],
            },
            "search_orders": {
                "version": "2.0.0",
                "deprecated": False,
                "format": "json",
            },
            "get_database_summary": {
                "version": "2.0.0",
                "deprecated": False,
                "format": "json",
            },
            "check_system_health": {
                "version": "2.0.0",
                "deprecated": False,
                "format": "json",
            },
        },
        "migration_guide": (
            "Upgrade client integrations to *_v2 tools to receive structured JSON objects. "
            "Legacy clients calling v1 tools will continue to receive string outputs with zero breaking changes."
        ),
    }
    return json.dumps(info_payload, indent=2, ensure_ascii=False)


# ── 5. Server Entrypoint ──────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description=f"{SERVER_NAME} runner")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "http"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="Transport type (stdio or streamable-http)",
    )
    parser.add_argument("--host", default=HOST, help="Host to bind for HTTP (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port for HTTP (default {PORT})")
    args = parser.parse_args()

    transport = "streamable-http" if args.transport in ("streamable-http", "http") else "stdio"

    if transport == "streamable-http":
        print(f"🚀 Starting {SERVER_NAME} v{SERVER_VERSION} on http://{args.host}:{args.port}/mcp (Streamable HTTP)", file=sys.stderr)
        print(f"🔑 Authentication enabled via Bearer token (TokenVerifier)", file=sys.stderr)
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        # Default stdio
        mcp.run()


if __name__ == "__main__":
    main()
