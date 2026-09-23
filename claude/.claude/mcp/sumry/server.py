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
    {
        "name": "sumry_planned",
        "description": "List planned (recurring or one-off future) transactions — rent, salary, subscriptions, savings transfers — with frequency, next date, monthly equivalent and a short id the other plan tools accept.",
        "inputSchema": {
            "type": "object",
            "properties": {"include_inactive": {"type": "boolean", "description": "Include paused plans."}},
        },
        "handler": tools.list_planned,
    },
    {
        "name": "sumry_upcoming",
        "description": "Dated occurrences of every active plan in the next N days, plus overdue ones (due but never booked). Use for 'what's coming up' or 'what bills are due'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "How far ahead, 1–366. Default 30."},
                "account": _ACCOUNT,
            },
        },
        "handler": tools.upcoming_planned,
    },
    {
        "name": "sumry_safe_to_spend",
        "description": "How much can be spent before the next planned income: balance minus planned expenses (and, for one account, transfers out) due until then, with a per-day figure. Use for 'can I afford X'.",
        "inputSchema": {
            "type": "object",
            "properties": {"account": {**_ACCOUNT, "description": "Limit to one account. Default: all accounts."}},
        },
        "handler": tools.safe_to_spend,
    },
    {
        "name": "sumry_plan_create",
        "description": "Plan a recurring or one-off future transaction. Pass category for an income/expense (the category's type sets the direction) or to_account for a planned transfer. A start date in the past treats earlier occurrences as already in the history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "e.g. 'Miete', 'Lohn', 'Spotify'."},
                "amount": {"type": "number", "description": "Positive amount in CHF."},
                "frequency": {"type": "string", "enum": ["DAILY", "WEEKLY", "MONTHLY", "YEARLY", "ONCE"]},
                "start_date": {"type": "string", "description": "YYYY-MM-DD of the first occurrence; later ones step from it."},
                "account": _ACCOUNT,
                "category": {"type": "string", "description": "Exact category label. Omit for a transfer."},
                "to_account": {**_ACCOUNT, "description": "Destination account — makes this a planned transfer."},
                "end_date": {"type": "string", "description": "YYYY-MM-DD of the last possible occurrence. Omit for indefinite."},
                "description": {"type": "string", "description": "Note written onto each booked occurrence. Defaults to the name."},
                "auto_book": {"type": "boolean", "description": "Book automatically when due. Default false (reminder only)."},
            },
            "required": ["name", "amount", "frequency", "start_date", "account"],
        },
        "handler": tools.create_plan,
    },
    {
        "name": "sumry_plan_update",
        "description": "Change a plan. Pass only the fields that change; active=false pauses it without deleting.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "8-char id from sumry_planned, full UUID, or the plan's name."},
                "name": {"type": "string"},
                "amount": {"type": "number"},
                "frequency": {"type": "string", "enum": ["DAILY", "WEEKLY", "MONTHLY", "YEARLY", "ONCE"]},
                "start_date": {"type": "string"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD, or an empty string to make it run indefinitely."},
                "account": _ACCOUNT,
                "category": {"type": "string", "description": "Switches a transfer plan to income/expense."},
                "to_account": {**_ACCOUNT, "description": "Switches the plan to a transfer into this account."},
                "description": {"type": "string"},
                "auto_book": {"type": "boolean"},
                "active": {"type": "boolean"},
            },
            "required": ["plan_id"],
        },
        "handler": tools.update_plan,
    },
    {
        "name": "sumry_plan_book",
        "description": "Book a plan's next due occurrence now as a real transaction (for manual, non-auto plans, or paying early). Books today if paid early.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "8-char id, full UUID, or the plan's name."},
                "date": {"type": "string", "description": "YYYY-MM-DD booking date override."},
            },
            "required": ["plan_id"],
        },
        "handler": tools.book_plan,
    },
    {
        "name": "sumry_plan_delete",
        "description": "Delete a plan for good. Already-booked transactions stay. Prefer sumry_plan_update active=false to pause.",
        "inputSchema": {
            "type": "object",
            "properties": {"plan_id": {"type": "string", "description": "8-char id, full UUID, or the plan's name."}},
            "required": ["plan_id"],
        },
        "handler": tools.delete_plan,
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
