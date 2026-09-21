#!/usr/bin/env python3
"""MCP server for Sumry, the self-hosted finance app at sumry.elyesghazel.ch.

Speaks JSON-RPC 2.0 over stdio using nothing but the standard library, so it
runs anywhere python3 does — no node, no uv, no virtualenv to keep in sync with
the dotfiles.

Credentials come from the environment (SUMRY_EMAIL / SUMRY_PASSWORD), injected
by `claude mcp add -e` from ~/.claude/secrets.fish. See
~/.claude/bin/mcp-bootstrap.fish.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tools  # noqa: E402
from client import SumryClient, SumryError  # noqa: E402

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "sumry", "version": "1.0.0"}

_client: SumryClient | None = None


def client() -> SumryClient:
    global _client
    if _client is None:
        _client = SumryClient()
    return _client


# ------------------------------------------------------------- tool schemas

_ACCOUNT = {
    "type": "string",
    "description": "Account name, an unambiguous prefix of it, or its UUID (e.g. 'PostFinance', 'cash').",
}
_DATE = {
    "type": "string",
    "description": "YYYY-MM-DD (or full ISO-8601). Defaults to now.",
}

TOOLS = [
    {
        "name": "sumry_accounts",
        "description": "List every account with its current balance and the total net worth. Start here when asked how much money there is.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tools.list_accounts,
    },
    {
        "name": "sumry_summary",
        "description": "Full picture for one month: net worth, per-account balances, income vs expenses, and the top spending categories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "YYYY-MM. Defaults to the current month."}
            },
        },
        "handler": tools.summary,
    },
    {
        "name": "sumry_trend",
        "description": "Income, expenses and net per month over the last N months — use for 'am I spending more than usual' questions.",
        "inputSchema": {
            "type": "object",
            "properties": {"months": {"type": "integer", "description": "How many months back. Default 6."}},
        },
        "handler": tools.monthly_trend,
    },
    {
        "name": "sumry_transactions",
        "description": "List transactions, newest first, with optional filters. Returns a short id per row that the update and delete tools accept.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": _ACCOUNT,
                "since": {"type": "string", "description": "Only on or after this YYYY-MM-DD."},
                "until": {"type": "string", "description": "Only on or before this YYYY-MM-DD."},
                "category": {"type": "string", "description": "Substring match on the category label."},
                "kind": {
                    "type": "string",
                    "description": "Comma-separated: INCOME, EXPENSE, TRANSFER_IN, TRANSFER_OUT.",
                },
                "search": {"type": "string", "description": "Substring match on the description."},
                "limit": {"type": "integer", "description": "Max rows. Default 25."},
            },
        },
        "handler": tools.list_transactions,
    },
    {
        "name": "sumry_categories",
        "description": "List the categories available for logging. Call this before logging if unsure which label exists — labels must match exactly.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "description": "INCOME or EXPENSE."},
                "include_inactive": {"type": "boolean", "description": "Include retired categories."},
            },
        },
        "handler": tools.list_categories,
    },
    {
        "name": "sumry_log",
        "description": "Log an income or expense. The direction comes from the category's own type, so always pass a positive amount.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Positive amount in CHF."},
                "category": {"type": "string", "description": "Exact category label, e.g. 'Lebensmittel'."},
                "account": _ACCOUNT,
                "description": {"type": "string", "description": "Short note, e.g. 'Migros'."},
                "date": _DATE,
            },
            "required": ["amount", "category", "account"],
        },
        "handler": tools.log_transaction,
    },
    {
        "name": "sumry_transfer",
        "description": "Move money between two of your own accounts. Books both legs, so it does not count as income or expense.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Positive amount in CHF."},
                "from_account": _ACCOUNT,
                "to_account": _ACCOUNT,
                "description": {"type": "string"},
                "date": _DATE,
            },
            "required": ["amount", "from_account", "to_account"],
        },
        "handler": tools.transfer,
    },
    {
        "name": "sumry_reconcile",
        "description": "Set an account to the balance the real bank or wallet shows. The gap is booked as an 'Einstellung' adjustment rather than silently overwritten, so history keeps adding up. Use this whenever a balance is stated as a fact rather than as a change.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": _ACCOUNT,
                "new_balance": {"type": "number", "description": "The real balance now, in CHF."},
                "note": {"type": "string", "description": "Why it differed. Defaults to 'Abgleich'."},
            },
            "required": ["account", "new_balance"],
        },
        "handler": tools.reconcile,
    },
    {
        "name": "sumry_update",
        "description": "Correct an existing transaction. Pass only the fields that change; the balance is recomputed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "Transaction id — the 8-char id from the transactions table or the full UUID."},
                "amount": {"type": "number"},
                "description": {"type": "string"},
                "category": {"type": "string"},
                "account": _ACCOUNT,
                "date": _DATE,
            },
            "required": ["transaction_id"],
        },
        "handler": tools.update_transaction,
    },
    {
        "name": "sumry_delete",
        "description": "Delete a transaction and revert its effect on the balance.",
        "inputSchema": {
            "type": "object",
            "properties": {"transaction_id": {"type": "string", "description": "The 8-char id from the transactions table or the full UUID."}},
            "required": ["transaction_id"],
        },
        "handler": tools.delete_transaction,
    },
    {
        "name": "sumry_budgets",
        "description": "Budget limits with how much of each is already spent this month.",
        "inputSchema": {
            "type": "object",
            "properties": {"month": {"type": "string", "description": "YYYY-MM. Defaults to now."}},
        },
        "handler": tools.list_budgets,
    },
    {
        "name": "sumry_create_account",
        "description": "Create a new account (a card, wallet, or savings pot).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "starting_balance": {"type": "number", "description": "Defaults to 0."},
            },
            "required": ["name"],
        },
        "handler": tools.create_account,
    },
]

HANDLERS = {t["name"]: t["handler"] for t in TOOLS}
PUBLIC_TOOLS = [{k: v for k, v in t.items() if k != "handler"} for t in TOOLS]


# ------------------------------------------------------------------- plumbing


def _write(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def _result(request_id, payload) -> None:
    _write({"jsonrpc": "2.0", "id": request_id, "result": payload})


def _error(request_id, code: int, message: str) -> None:
    _write({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def _text(body: str, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": body}], "isError": is_error}


def handle(request: dict) -> None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    # Notifications carry no id and must never be answered.
    if request_id is None:
        return

    if method == "initialize":
        requested = params.get("protocolVersion")
        _result(
            request_id,
            {
                "protocolVersion": requested if isinstance(requested, str) else PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            },
        )
    elif method == "ping":
        _result(request_id, {})
    elif method == "tools/list":
        _result(request_id, {"tools": PUBLIC_TOOLS})
    elif method == "tools/call":
        name = params.get("name")
        handler = HANDLERS.get(name)
        if handler is None:
            _error(request_id, -32602, f"Unknown tool: {name}")
            return
        try:
            body = handler(client(), **(params.get("arguments") or {}))
            _result(request_id, _text(body))
        except SumryError as exc:
            # A failed call is a tool-level result, not a protocol error, so the
            # model sees the reason and can correct itself.
            _result(request_id, _text(f"Sumry error: {exc}", is_error=True))
        except TypeError as exc:
            _result(request_id, _text(f"Bad arguments for {name}: {exc}", is_error=True))
        except Exception as exc:  # noqa: BLE001
            _result(request_id, _text(f"{type(exc).__name__}: {exc}", is_error=True))
    else:
        _error(request_id, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except ValueError:
            _error(None, -32700, "Parse error")
            continue
        handle(request)


if __name__ == "__main__":
    main()
