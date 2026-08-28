"""Master Test Runner for DevOps & Database Intelligence MCP Server.

Executes:
1. Tool Unit Tests (Logs, Database, System)
2. Authentication & TokenVerifier Tests
3. Versioning & Server Metadata Tests
4. Stdio Client End-to-End Integration
5. Streamable HTTP Server & Auth Rejection Test
6. Smart Client Discovery & Fallback Test
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from tests.test_auth import TestDevOpsAuth
from tests.test_tools import TestDatabaseTools, TestLogTools, TestSystemTools
from tests.test_versioning import TestServerVersioning


def run_unit_tests() -> bool:
    """Run all unit test suites via unittest runner."""
    print("=" * 70)
    print("🧪 1. RUNNING UNIT TESTS (Tools, Auth, Versioning)")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLogTools))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseTools))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemTools))
    suite.addTests(loader.loadTestsFromTestCase(TestDevOpsAuth))
    suite.addTests(loader.loadTestsFromTestCase(TestServerVersioning))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_stdio_integration() -> bool:
    """Run the stdio client integration test."""
    print("\n" + "=" * 70)
    print("🔌 2. RUNNING STDIO CLIENT INTEGRATION TEST")
    print("=" * 70)

    client_path = BASE_DIR / "clients" / "client_stdio.py"
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = str(BASE_DIR)

    proc = subprocess.run(
        [sys.executable, str(client_path)],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(f"❌ Stdio test failed: {proc.stderr}")
        return False
    return True


def run_smart_client_integration() -> bool:
    """Run the smart client version negotiation integration test."""
    print("\n" + "=" * 70)
    print("🧠 3. RUNNING SMART CLIENT VERSIONING TEST")
    print("=" * 70)

    client_path = BASE_DIR / "clients" / "client_smart.py"
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = str(BASE_DIR)

    proc = subprocess.run(
        [sys.executable, str(client_path)],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(f"❌ Smart client test failed: {proc.stderr}")
        return False
    return True


def run_http_auth_integration() -> bool:
    """Start HTTP server temporarily, run HTTP auth client test, and stop server."""
    print("\n" + "=" * 70)
    print("🔐 4. RUNNING STREAMABLE HTTP & AUTH INTEGRATION TEST")
    print("=" * 70)

    server_path = BASE_DIR / "server.py"
    client_path = BASE_DIR / "clients" / "client_http.py"

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = str(BASE_DIR)
    env["MCP_PORT"] = "8089"

    # Start HTTP server on port 8089
    server_proc = subprocess.Popen(
        [sys.executable, str(server_path), "--transport", "streamable-http", "--port", "8089"],
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    time.sleep(2.0)  # Wait for server startup

    try:
        env_client = env.copy()
        env_client["PORT"] = "8089"
        client_proc = subprocess.run(
            [sys.executable, str(client_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env_client,
        )
        print(client_proc.stdout)
        if client_proc.returncode != 0:
            print(f"❌ HTTP client test failed: {client_proc.stderr}")
            return False
        return True
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3.0)
        except Exception:
            server_proc.kill()


def main() -> None:
    print("🚀 STARTING FULL TEST SUITE FOR DEVOPS MCP SERVER")
    t0 = time.time()

    success_unit = run_unit_tests()
    success_stdio = run_stdio_integration()
    success_smart = run_smart_client_integration()
    success_http = run_http_auth_integration()

    duration = round(time.time() - t0, 2)
    all_passed = success_unit and success_stdio and success_smart and success_http

    print("\n" + "=" * 70)
    print("📋 COMPREHENSIVE TEST RESULTS REPORT")
    print("=" * 70)
    print(f"  1. Unit Tests (Tools, Auth, Versioning) : {'✅ PASSED' if success_unit else '❌ FAILED'}")
    print(f"  2. Stdio Client End-to-End Test         : {'✅ PASSED' if success_stdio else '❌ FAILED'}")
    print(f"  3. Smart Client (server://info discovery): {'✅ PASSED' if success_smart else '❌ FAILED'}")
    print(f"  4. Streamable HTTP + Auth (3 Scenarios) : {'✅ PASSED' if success_http else '❌ FAILED'}")
    print(f"  Total Duration: {duration}s")
    print("=" * 70)

    if all_passed:
        print("🎉 ALL TEST SUITES PASSED WITH 100% SUCCESS!")
        sys.exit(0)
    else:
        print("❌ SOME TEST SUITES FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
