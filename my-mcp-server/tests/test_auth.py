"""Unit and Integration tests for DevOps MCP Server Authentication."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

# Ensure parent directory is in sys.path
PARENT_DIR = Path(__file__).resolve().parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from config import DEFAULT_AUTH_TOKEN, PROD_AUTH_TOKEN
from server import DevOpsTokenVerifier


class TestDevOpsAuth(unittest.IsolatedAsyncioTestCase):
    """Test Bearer Token authentication provider and verification."""

    async def asyncSetUp(self) -> None:
        self.verifier = DevOpsTokenVerifier()

    async def test_valid_default_token(self) -> None:
        """Test verifying the default development token."""
        access_token = await self.verifier.verify_token(DEFAULT_AUTH_TOKEN)
        self.assertIsNotNone(access_token)
        self.assertEqual(access_token.token, DEFAULT_AUTH_TOKEN)
        self.assertEqual(access_token.client_id, "developer-local")
        self.assertIn("logs:read", access_token.scopes)

    async def test_valid_prod_token(self) -> None:
        """Test verifying production token."""
        access_token = await self.verifier.verify_token(PROD_AUTH_TOKEN)
        self.assertIsNotNone(access_token)
        self.assertEqual(access_token.client_id, "production-admin")
        self.assertIn("admin:full", access_token.scopes)

    async def test_invalid_token(self) -> None:
        """Test verifying an unauthorized token returns None."""
        access_token = await self.verifier.verify_token("completely_invalid_token_999")
        self.assertIsNone(access_token)

    async def test_empty_token(self) -> None:
        """Test empty token returns None."""
        access_token = await self.verifier.verify_token("")
        self.assertIsNone(access_token)


if __name__ == "__main__":
    unittest.main()
