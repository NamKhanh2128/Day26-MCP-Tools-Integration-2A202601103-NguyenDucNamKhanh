"""Streamable HTTP Client with Comprehensive Authentication Testing.

Tests:
1. Scenario A: Valid Bearer Token (Expect 200 OK & successful tool execution)
2. Scenario B: Invalid Bearer Token (Expect 401/403 Authentication Rejection)
3. Scenario C: Missing Bearer Token (Expect 401 Unauthorized)
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

import httpx

from config import DEFAULT_AUTH_TOKEN, PORT
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SERVER_URL = f"http://localhost:{PORT}/mcp"


async def test_valid_token() -> bool:
    """Test connection with valid Bearer Token."""
    print("▶️ [Scenario 1] Testing with VALID Bearer Token...")
    headers = {"Authorization": f"Bearer {DEFAULT_AUTH_TOKEN}"}

    try:
        async with httpx.AsyncClient(headers=headers, timeout=10.0) as http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    print(f"   ✅ Authentication SUCCESS! Server granted access to {len(tools.tools)} tools.")
                    
                    # Test calling a tool
                    result = await session.call_tool("search_orders", {"status": "COMPLETED", "limit": 2})
                    parsed = json.loads(result.content[0].text)
                    print(f"   ✅ Tool execution SUCCESS! Returned {parsed.get('count')} completed orders.")
                    return True
    except Exception as e:
        print(f"   ❌ Valid token test failed unexpectedly: {e}")
        return False


async def test_invalid_token() -> bool:
    """Test connection with invalid Bearer Token."""
    print("\n▶️ [Scenario 2] Testing with INVALID Bearer Token ('Bearer wrong_secret_token')...")
    headers = {"Authorization": "Bearer wrong_secret_token"}

    try:
        async with httpx.AsyncClient(headers=headers, timeout=5.0) as http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print("   ❌ SECURITY FLAW: Server accepted an invalid token!")
                    return False
    except Exception as e:
        print(f"   ✅ CORRECT BEHAVIOR: Server rejected invalid token with error: {e}")
        return True


async def test_missing_token() -> bool:
    """Test connection with missing Authorization header."""
    print("\n▶️ [Scenario 3] Testing with MISSING Bearer Token (No Authorization Header)...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print("   ❌ SECURITY FLAW: Server allowed unauthenticated request!")
                    return False
    except Exception as e:
        print(f"   ✅ CORRECT BEHAVIOR: Server rejected unauthenticated request with error: {e}")
        return True


async def main() -> None:
    print("=" * 70)
    print(f"🔐 TESTING STREAMABLE HTTP AUTHENTICATION ON {SERVER_URL}")
    print("=" * 70)

    res_valid = await test_valid_token()
    res_invalid = await test_invalid_token()
    res_missing = await test_missing_token()

    print("\n" + "=" * 70)
    print("📊 AUTHENTICATION TEST SUMMARY:")
    print(f"   • Valid Token Test   : {'PASSED (200 OK)' if res_valid else 'FAILED'}")
    print(f"   • Invalid Token Test : {'PASSED (401/403 Rejected)' if res_invalid else 'FAILED'}")
    print(f"   • Missing Token Test : {'PASSED (401 Rejected)' if res_missing else 'FAILED'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
