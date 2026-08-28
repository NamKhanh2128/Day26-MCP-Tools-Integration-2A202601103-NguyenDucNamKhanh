"""Configuration module for DevOps & Database Intelligence MCP Server."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Server Metadata
SERVER_NAME = os.getenv("MCP_SERVER_NAME", "devops-mcp-server")
SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "2.1.0")
PROTOCOL_VERSION = "MCP/2024-11-05"

# Network & Transport
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("MCP_PORT", "8080")))

# Authentication Tokens
DEFAULT_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "dev-token-secret123")
PROD_AUTH_TOKEN = os.getenv("MCP_PROD_TOKEN", "prod-token-xyz999")

VALID_TOKENS: dict[str, dict[str, str | list[str]]] = {
    DEFAULT_AUTH_TOKEN: {
        "client_id": "developer-local",
        "role": "developer",
        "scopes": ["logs:read", "db:read", "system:read"],
    },
    PROD_AUTH_TOKEN: {
        "client_id": "production-admin",
        "role": "admin",
        "scopes": ["logs:read", "db:read", "system:read", "admin:full"],
    },
}

# File & Data Paths
DATA_DIR = BASE_DIR / "data"

def _resolve_path(env_var: str, default: Path) -> Path:
    val = os.getenv(env_var)
    if not val:
        return default
    p = Path(val)
    if p.is_absolute():
        return p
    return (BASE_DIR / p).resolve()

LOG_FILE_PATH = _resolve_path("APP_LOG_PATH", DATA_DIR / "sample_app.log")
ORDERS_JSON_PATH = _resolve_path("ORDERS_JSON_PATH", DATA_DIR / "sample_orders.json")
SQLITE_DB_PATH = _resolve_path("SQLITE_DB_PATH", DATA_DIR / "app_database.db")

# External Database (e.g. Supabase PostgreSQL if provided)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:123456789%40%40KAI**%23%23@db.bmnnykrmesauqaikbcot.supabase.co:5432/postgres"
)
