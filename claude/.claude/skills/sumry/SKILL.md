---
name: sumry
description: Read and write the self-hosted Sumry finances at sumry.elyesghazel.ch through the sumry MCP server. Use whenever the user mentions money, their balance, an account (PostFinance, Revolut, Sparkonto, Portemonnaie / Cash), what they spent, what they earned, whether they can afford something, budgets, or asks to log, book, record, or correct a transaction — including bare statements like "spent 12.50 on lunch", "got paid", "PostFinance is at 334.50", or "add 460 to cash". Also use for questions about spending trends, where the money went this month, and net worth.
---

# Sumry

Elyes' self-hosted finance app. The `sumry` MCP server talks to the Spring backend at
`sumry-api.elyesghazel.ch`; the web UI lives at `sumry.elyesghazel.ch`. Everything is CHF.

## Tools

| Tool | Use |
|---|---|
| `sumry_accounts` | Balances + net worth. The cheapest way to answer "how much do I have" |
| `sumry_summary` | One month: net worth, balances, income vs expenses, top categories |
| `sumry_trend` | Income/expense/net per month — for "is this month unusual" |
| `sumry_transactions` | Filtered list, newest first; returns ids for corrections |
| `sumry_categories` | Valid category labels — labels must match exactly when logging |
| `sumry_log` | Book an income or expense |
| `sumry_transfer` | Move money between two own accounts |
| `sumry_reconcile` | Set an account to its real balance; books the gap as an adjustment |
| `sumry_update` / `sumry_delete` | Correct or remove a transaction |
| `sumry_budgets` | Limits and how much is spent against them |
| `sumry_create_account` | New account |

Accounts resolve by name, so pass `"cash"` or `"PostFinance"` — never make the user find a UUID.

## The one distinction that matters

Sumry's balances are derived from history, so **how** a balance changes decides the tool:

- **A change** — "spent 12.50 on coffee", "got 300 from a sale" → `sumry_log`.
- **A fact** — "PostFinance is at 334.50", "cash is 580 now" → `sumry_reconcile`.
  It books the difference as an `Einstellung` adjustment so the transactions still add up to
  the balance. Never fix a balance by inventing a plausible expense.
- **Money that moved between own accounts** — "took 200 out of the machine", "moved 500 to
  savings" → `sumry_transfer`, so it does not distort income or expenses.

"Add 460 to cash" is ambiguous: it is a *delta*, but with no category it cannot be an
honest expense or income. Read the current balance, then `sumry_reconcile` to
`current + 460` with a note saying where it came from.

## Logging well

1. `sumry_categories` first if the label is not obviously one you have seen — the API 404s on
   an unknown label rather than creating one.
2. Amounts are always positive; the category's own type (INCOME or EXPENSE) sets the direction.
3. Default account is PostFinance unless the user says cash, Revolut, or savings.
4. Dates default to now. "yesterday", "on the 3rd" → pass an explicit `YYYY-MM-DD`.
5. Batch: several purchases in one sentence are several `sumry_log` calls, not a summed one.

Only ask before writing when something is genuinely ambiguous — the amount, which account, or
which of log/reconcile/transfer applies. A clear "spent 8 on a kebab" just gets logged.

## Answering money questions

Lead with the number, then the one fact that explains it. `sumry_summary` already ranks the
top categories, so read the cause off that rather than dumping the whole transaction list.
When a month looks alarming, check `sumry_trend` before saying so — a single large purchase
is not a spending problem, and saying it is would be wrong.

Known shape of the data: salary (`Lohn`) lands monthly, `SlidePlate Einnahmen` is side
income, and `Auto & Töffli` swings hard when there is vehicle work.

## Setup

Credentials come from `~/.claude/secrets.fish` (gitignored):

```fish
set -gx SUMRY_API_URL  "https://sumry-api.elyesghazel.ch"
set -gx SUMRY_EMAIL    "..."
set -gx SUMRY_PASSWORD "..."
```

Then `fish ~/.claude/bin/mcp-bootstrap.fish`. The server is stdlib-only Python at
`~/.claude/mcp/sumry/`; it logs in on first call, caches the JWT in memory, and re-logs in on
a 401. If a tool reports missing credentials, that file is the thing to fix.

## Direct database access

The API is the interface. Only fall back to
`docker exec apps-sumry-db psql -U sumry -d sumry` on the server itself for read-only
analysis the API cannot express — and dump first (`db-dump/`) before any write, because
writing SQL directly bypasses the balance recomputation the backend does.
