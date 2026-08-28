# DevOps & Database Intelligence MCP Server

A production-ready Model Context Protocol (MCP) server designed to automate everyday developer & DevOps workflows: **Log Diagnostics & Anomaly Detection**, **Database Inspection & Order Intelligence**, and **System Infrastructure Telemetry**.

---

## 🌟 Architecture & Capabilities

```mermaid
graph TD
    Client["MCP Client (Claude Code / Claude Desktop / Custom Agent)"]
    
    subgraph Transports
        Stdio["stdio Transport (Local CLI/IDE)"]
        HTTP["Streamable HTTP (Remote / LAN)"]
    end
    
    subgraph Security Layer
        Auth["TokenVerifier (Bearer Token Auth)"]
    end
    
    subgraph Server Core ["devops-mcp-server (v2.1.0)"]
        Meta["server://info (Metadata & Migration Guide)"]
        LogTools["Log Diagnostics (v1 + v2)"]
        DBTools["Database & Order Intelligence (v1 + v2)"]
        SysTools["System Telemetry (check_system_health)"]
    end
    
    Client --> Stdio --> Server Core
    Client --> HTTP --> Auth --> Server Core
```

---

## 🛠️ Tools Inventory

| Category | Tool | Version | Status | Description |
|---|---|---|---|---|
| **Logs** | `search_logs(keyword, level, limit)` | `1.0.0` | ⚠️ Deprecated | Legacy plain-text log search. |
| **Logs** | `search_logs_v2(keyword, level, limit, include_metrics)` | `2.1.0` | ✅ Active | Structured JSON log analytics, error rate breakdown, and anomaly detection. |
| **Logs** | `get_recent_errors(limit, include_stacktrace)` | `2.0.0` | ✅ Active | Extracts recent `ERROR` & `CRITICAL` entries with full stack traces. |
| **Logs** | `get_log_summary()` | `2.0.0` | ✅ Active | Aggregates log metrics, time range, and top active modules. |
| **Database** | `get_order(order_id)` | `1.0.0` | ⚠️ Deprecated | Legacy text order lookup. |
| **Database** | `get_order_v2(order_id, include_items, include_customer)` | `2.1.0` | ✅ Active | Rich JSON order inspection with itemization and delivery tracking. |
| **Database** | `search_orders(status, min_amount, limit)` | `2.0.0` | ✅ Active | Filter orders by status (`COMPLETED`, `PROCESSING`, `PENDING_PAYMENT`, `CANCELLED`). |
| **Database** | `get_database_summary()` | `2.0.0` | ✅ Active | Database schema overview, estimated rows, and revenue analytics. |
| **System** | `check_system_health()` | `2.0.0` | ✅ Active | Host CPU, RAM, Disk, process uptime, and storage health. |

---

## 📚 Resources

| Resource URI | Description |
|---|---|
| `server://info` | Returns server metadata, protocol version (`MCP/2024-11-05`), tool deprecation map, and migration guide. |

---

## 🚀 Quick Start Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run in `stdio` Mode (Local CLI / Claude Code)

```bash
python server.py --transport stdio
```

### 3. Run in `Streamable HTTP` Mode with Bearer Auth

```bash
python server.py --transport streamable-http --port 8080
```

The server listens on `http://0.0.0.0:8080/mcp`.

---

## 🧪 Testing & Verification

### One-Click Master Test Runner

```bash
python run_all_tests.py
```

Runs:
1. **Unit Tests**: 15 unit tests covering all tools, TokenVerifier, and server metadata.
2. **Stdio Integration**: End-to-end tool discovery and calls via standard I/O.
3. **Smart Client**: Discovery via `server://info` and auto-negotiation between v1 and v2.
4. **Streamable HTTP Auth**:
   - ✅ Valid token (`dev-token-secret123`) -> 200 OK & tool call.
   - 🚫 Invalid token (`wrong_secret_token`) -> Rejected (401/403).
   - 🚫 Missing token -> Rejected (401 Unauthorized).

---

## 🤖 Integration with Claude Code & Claude Desktop

### Option 1: Claude Code CLI

```bash
claude mcp add devops-intelligence -- python c:/Users/KHANH/Documents/GitHub/Day26-MCP-Tools-Integration-2A202601103-NguyenDucNamKhanh/my-mcp-server/server.py --transport stdio
```

### Option 2: Claude Desktop Config (`claude_desktop_config.json`)

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devops-intelligence": {
      "command": "python",
      "args": [
        "c:/Users/KHANH/Documents/GitHub/Day26-MCP-Tools-Integration-2A202601103-NguyenDucNamKhanh/my-mcp-server/server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONUTF8": "1",
        "MCP_AUTH_TOKEN": "dev-token-secret123"
      }
    }
  }
}
```

### Natural Language Test Queries in Claude:
- *"Tìm giúp tôi các sự cố database timeout trong log và đưa ra giải pháp khắc phục."*
- *"Tra cứu đơn hàng ORD-2026-001 xem có những sản phẩm gì và trạng thái giao hàng thế nào."*
- *"Kiểm tra tổng doanh thu các đơn hàng đã hoàn tất trong database."*
- *"Kiểm tra tình trạng sức khỏe hệ thống và dung lượng đĩa còn trống."*
