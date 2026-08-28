"""Log Analytics & Anomaly Detection Tools.

Provides search, diagnostic, and error extraction capabilities over application logs.
Demonstrates tool versioning with backward compatibility:
- search_logs: v1 legacy tool (returns plain formatted text).
- search_logs_v2: v2 enhanced tool (returns structured JSON with metrics and anomalies).
- get_recent_errors: Error extractor with stack traces.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from config import LOG_FILE_PATH

# Log regex pattern matching: "2026-08-28 08:00:15 [INFO] [server.main] Application startup..."
LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(?P<level>[A-Z]+)\]\s+\[(?P<module>[a-zA-Z0-9_\.]+)\]\s+(?P<message>.*)$"
)


def _read_and_parse_logs(file_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Helper to parse log file into structured records including stack traces."""
    path = Path(file_path or LOG_FILE_PATH)
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    current_record: dict[str, Any] | None = None

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.rstrip("\r\n")
            match = LOG_PATTERN.match(stripped)
            if match:
                if current_record:
                    records.append(current_record)
                current_record = {
                    "timestamp": match.group("timestamp"),
                    "level": match.group("level").upper(),
                    "module": match.group("module"),
                    "message": match.group("message"),
                    "stacktrace": [],
                }
            else:
                # Continuation line or stack trace
                if current_record:
                    current_record["stacktrace"].append(stripped)
                else:
                    # Header/unformatted line
                    current_record = {
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "level": "INFO",
                        "module": "system",
                        "message": stripped,
                        "stacktrace": [],
                    }

    if current_record:
        records.append(current_record)

    return records


# ── Tool v1: search_logs (Legacy format - Backward compatible) ─────────
def search_logs(keyword: str = "", level: str = "ALL", limit: int = 50) -> str:
    """[v1] Search application logs by keyword and log level.
    
    Returns plain text lines for legacy MCP clients.
    Deprecated: Prefer search_logs_v2 for structured JSON output and anomaly insights.

    Args:
        keyword: Substring or term to search for (e.g., "error", "database", "ORD-").
        level: Minimum log level filter: "ALL", "INFO", "WARNING", "ERROR", "CRITICAL".
        limit: Maximum number of log lines to return (default 50).
    """
    records = _read_and_parse_logs()
    filtered = []
    level_filter = level.upper()

    for rec in records:
        if level_filter != "ALL" and rec["level"] != level_filter:
            continue
        full_text = f"{rec['message']} {' '.join(rec['stacktrace'])}"
        if keyword and keyword.lower() not in full_text.lower() and keyword.lower() not in rec["module"].lower():
            continue
        
        line_repr = f"{rec['timestamp']} [{rec['level']}] [{rec['module']}] {rec['message']}"
        if rec["stacktrace"]:
            line_repr += f"\n  Stacktrace: {' '.join(rec['stacktrace'][:3])}..."
        filtered.append(line_repr)

        if len(filtered) >= limit:
            break

    if not filtered:
        return f"No log entries found matching keyword='{keyword}' and level='{level}'."

    header = f"=== Log Search Results ({len(filtered)} matches) ==="
    return header + "\n" + "\n".join(filtered)


# ── Tool v2: search_logs_v2 (Modern Structured JSON format) ──────────
def search_logs_v2(
    keyword: str = "",
    level: str = "ALL",
    limit: int = 50,
    include_metrics: bool = True,
) -> str:
    """[v2] Advanced search and diagnostic analysis on application logs.
    
    Returns rich JSON format including log breakdown, stack traces, anomaly detection,
    and automated troubleshooting recommendations.

    Args:
        keyword: Substring or regex term to search (e.g., "payment", "timeout", "circuit_breaker").
        level: Level filter: "ALL", "INFO", "WARNING", "ERROR", "CRITICAL" (default "ALL").
        limit: Max entries to return (default 50).
        include_metrics: Whether to include summary metrics and anomaly detection (default True).
    """
    records = _read_and_parse_logs()
    filtered: list[dict[str, Any]] = []
    level_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
    anomalies: list[dict[str, str]] = []
    recommendations: list[str] = []

    level_filter = level.upper()

    for rec in records:
        rec_level = rec["level"]
        if rec_level in level_counts:
            level_counts[rec_level] += 1

        if level_filter != "ALL" and rec_level != level_filter:
            continue

        full_text = f"{rec['message']} {' '.join(rec['stacktrace'])}"
        if keyword and keyword.lower() not in full_text.lower() and keyword.lower() not in rec["module"].lower():
            continue

        # Anomaly detection triggers
        if "timeout" in full_text.lower() or "pool exhausted" in full_text.lower():
            anomalies.append({
                "type": "DATABASE_PRESSURE",
                "severity": "HIGH",
                "evidence": f"Timestamp {rec['timestamp']}: {rec['message']}",
            })
            if "Increase connection pool size or check for unindexed long-running queries" not in recommendations:
                recommendations.append("Increase connection pool size or check for unindexed long-running queries.")

        if "kms" in full_text.lower() or "keynotfound" in full_text.lower():
            anomalies.append({
                "type": "SECURITY_CONFIG_ERROR",
                "severity": "CRITICAL",
                "evidence": f"Timestamp {rec['timestamp']}: {rec['message']}",
            })
            if "Verify KMS keyring permissions and secret key rotation schedules" not in recommendations:
                recommendations.append("Verify KMS keyring permissions and secret key rotation schedules.")

        if len(filtered) < limit:
            filtered.append(rec)

    response_payload: dict[str, Any] = {
        "api_version": "2.1.0",
        "query": {"keyword": keyword, "level": level, "limit": limit},
        "total_matches": len(filtered),
        "results": filtered,
    }

    if include_metrics:
        response_payload["metrics"] = {
            "total_logs_analyzed": len(records),
            "level_distribution": level_counts,
            "error_rate_percent": round(
                ((level_counts["ERROR"] + level_counts["CRITICAL"]) / max(len(records), 1)) * 100, 2
            ),
        }
        response_payload["anomalies_detected"] = anomalies
        response_payload["remediation_recommendations"] = recommendations

    return json.dumps(response_payload, indent=2, ensure_ascii=False)


# ── Tool: get_recent_errors ──────────────────────────────────────────
def get_recent_errors(limit: int = 10, include_stacktrace: bool = True) -> str:
    """Extract and analyze the most recent ERROR and CRITICAL issues.

    Args:
        limit: Number of error records to return (default 10).
        include_stacktrace: Whether to include full multi-line stack traces (default True).
    """
    records = _read_and_parse_logs()
    error_records = [r for r in records if r["level"] in ("ERROR", "CRITICAL")]
    recent_errors = error_records[-limit:] if limit > 0 else error_records

    results = []
    for rec in reversed(recent_errors):
        item: dict[str, Any] = {
            "timestamp": rec["timestamp"],
            "level": rec["level"],
            "module": rec["module"],
            "error_message": rec["message"],
        }
        if include_stacktrace and rec["stacktrace"]:
            item["stacktrace"] = rec["stacktrace"]
        results.append(item)

    payload = {
        "api_version": "2.1.0",
        "error_count": len(results),
        "errors": results,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ── Tool: get_log_summary ────────────────────────────────────────────
def get_log_summary() -> str:
    """Return high-level summary metrics of the entire application log."""
    records = _read_and_parse_logs()
    if not records:
        return json.dumps({"status": "empty", "total_records": 0})

    modules: dict[str, int] = {}
    levels: dict[str, int] = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}

    for rec in records:
        mod = rec["module"]
        modules[mod] = modules.get(mod, 0) + 1
        lvl = rec["level"]
        if lvl in levels:
            levels[lvl] += 1

    summary = {
        "api_version": "2.1.0",
        "log_file": str(LOG_FILE_PATH.name),
        "total_records": len(records),
        "time_range": {
            "start": records[0]["timestamp"],
            "end": records[-1]["timestamp"],
        },
        "levels": levels,
        "top_active_modules": sorted(modules.items(), key=lambda x: x[1], reverse=True)[:5],
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)
