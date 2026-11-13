"""More Sumry tools: statement import, the needs-you inbox, plan skip/postpone, bulk
recategorise, rules, account detail, goals, the monthly statement and subscriptions.

Same conventions as tools.py: Markdown out, names in (accounts, plans), short ids printed.
"""

from __future__ import annotations

import base64
import datetime as dt
import secrets
import time
from pathlib import Path

from client import SumryClient, SumryError
from tools import (
    CURRENCY,
    _accounts,
    _day,
    money,
    resolve_account,
    resolve_plan_id,
    resolve_transaction_id,
    table,
)

RECONCILE_AFTER_DAYS = 14
MAX_IMPORT_BYTES = 10 * 1024 * 1024
WINDOW_DAYS = 7

# Previews live in this process so sumry_import_commit can book them without re-uploading.
_IMPORTS: dict[str, dict] = {}


def _signed(kind: str | None, amount) -> str:
    sign = "+" if kind in ("INCOME", "TRANSFER_IN") else "−"
    return f"{sign}{money(amount)}"


def _cut(text: str | None, n: int = 60) -> str:
    t = (text or "—").replace("|", "/").replace("\n", " ").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


# ------------------------------------------------------------------ import


def _format_for(path: Path) -> tuple[str, bool]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "postfinance-pdf", True
    if ext in (".xml", ".053"):
        return "camt053", True
    if ext in (".csv", ".txt"):
        return "auto", False
    raise SumryError(f"{path.name}: use a PDF statement, a camt.053 XML or a CSV export.")


def import_preview(client: SumryClient, file, account, **_) -> str:
    path = Path(file).expanduser()
    if not path.is_file():
        raise SumryError(f"No file at {path}.")
    if path.stat().st_size > MAX_IMPORT_BYTES:
        raise SumryError(f"{path.name} is over 10 MB.")
    fmt, binary = _format_for(path)
    acc = resolve_account(client, account)
    body = {"accountId": acc["id"], "format": fmt, "fileName": path.name}
    if binary:
        body["fileBase64"] = base64.b64encode(path.read_bytes()).decode()
    else:
        body["csv"] = path.read_text(encoding="utf-8", errors="replace")
    p = client.post("/api/import/preview", body)

    rows = p.get("rows") or []
    import_id = secrets.token_hex(3)
    _IMPORTS[import_id] = {"accountId": acc["id"], "accountName": acc.get("accountName"), "preview": p, "at": time.time()}
    for k in [k for k, v in _IMPORTS.items() if time.time() - v["at"] > 6 * 3600]:
        _IMPORTS.pop(k, None)

    matched = [r for r in rows if r.get("duplicate")]
    new = [r for r in rows if not r.get("duplicate")]
    out = [f"## Import preview `{import_id}` → {acc.get('accountName')}", ""]
    period = f"{p.get('statementFrom') or '?'} – {p.get('statementTo') or '?'}"
    out.append(
        f"Format **{p.get('format')}** · period {period} · opening {money(p.get('statementOpeningBalance'))} · "
        f"closing {money(p.get('statementClosingBalance'))} · **{len(rows)} rows: {len(matched)} already logged, {len(new)} new**"
    )
    ok = p.get("balanceOk")
    if ok is True:
        out.append("Rows add up: ✓ opening + rows = closing, every booking was read.")
    elif ok is False:
        out.append(
            f"Rows add up: ✗ opening + rows = {money(p.get('computedClosingBalance'))}, statement says "
            f"{money(p.get('statementClosingBalance'))}. The reader missed or misread something."
        )
    notes = [w for w in (p.get("warnings") or []) if not w.lower().lstrip().startswith("diagnostics")]
    if notes:
        out.append("Warnings: " + "; ".join(notes[:6]))
    if any(w.lower().lstrip().startswith("diagnostics") for w in (p.get("warnings") or [])):
        out.append("The file could not be read fully; the preview carries a redacted diagnostics block.")

    out += ["", "### New rows (not matched to any entry)"]
    out.append(table(
        ["Line", "Date", "Booked", "Text", "CHF", "Rule category"],
        [[r["line"], r["date"], r.get("bookingDate") or "", _cut(r.get("description")), _signed(r.get("kind"), r.get("amount")), r.get("categoryLabel") or "—"] for r in new],
        {4},
    ))
    if matched:
        out += ["", "### Already logged"]
        out.append(table(
            ["Line", "Date", "CHF", "Matched"],
            [[r["line"], r["date"], _signed(r.get("kind"), r.get("amount")), _cut(r.get("matchNote") or "same amount nearby", 70)] for r in matched],
            {2},
        ))

    # The entries nothing matched, so the open rows can be checked against them right here.
    if new:
        used = {i for r in matched for i in (r.get("matchIds") or ([r["duplicateOfId"]] if r.get("duplicateOfId") else []))}
        days = [r["date"] for r in rows] + [r["bookingDate"] for r in rows if r.get("bookingDate")]
        lo = (dt.date.fromisoformat(min(days)) - dt.timedelta(days=WINDOW_DAYS)).isoformat()
        hi = (dt.date.fromisoformat(max(days)) + dt.timedelta(days=WINDOW_DAYS)).isoformat()
        entries = [
            t for t in (client.get("/api/transactions/") or [])
            if t.get("userAccountId") == acc["id"] and t.get("id") not in used and lo <= _day(t.get("date")) <= hi
        ]
        entries.sort(key=lambda t: _day(t.get("date")))
        out += ["", f"### Entries on {acc.get('accountName')} {lo} – {hi} that matched no row"]
        out.append(table(
            ["Id", "Date", "CHF", "Category", "Note"],
            [[t["id"][:8], _day(t.get("date")), _signed(t.get("kind"), t.get("amount")), t.get("categoryLabel") or "—", _cut(t.get("description"), 50)] for t in entries],
            {2},
        ))
        out += [
            "",
            "Before booking: pair open rows with these entries (wording differs, 1-3 days off, EUR conversions, "
            "payment + fee). Entries in category 'Einstellung' are reconcile adjustments; if new rows are what one "
            "covered, booking them counts that money twice, so suggest deleting the adjustment (sumry_delete). "
            "Then book with sumry_import_commit and show Elyes the plan first.",
        ]
    return "\n".join(out)


def import_commit(
    client: SumryClient, import_id, lines=None, categories=None, default_expense_category=None,
    default_income_category=None, **_
) -> str:
    saved = _IMPORTS.get((import_id or "").strip())
    if not saved:
        raise SumryError(f"No preview `{import_id}` in this session (they last 6 h). Run sumry_import again.")
    rows = saved["preview"].get("rows") or []
    if lines:
        wanted = {int(x) for x in lines}
        chosen = [r for r in rows if r["line"] in wanted]
        missing = wanted - {r["line"] for r in chosen}
        if missing:
            raise SumryError(f"Lines not in the preview: {sorted(missing)}")
    else:
        chosen = [r for r in rows if not r.get("duplicate")]
    if not chosen:
        raise SumryError("Nothing to book.")
    cats = {int(k): v for k, v in (categories or {}).items()}
    body = {
        "accountId": saved["accountId"],
        "rows": [
            {
                "line": r["line"], "date": r["date"], "description": r.get("description"), "amount": r["amount"],
                "kind": r["kind"], "categoryLabel": cats.get(r["line"]) or r.get("categoryLabel"),
            }
            for r in chosen
        ],
        "defaultExpenseCategory": default_expense_category,
        "defaultIncomeCategory": default_income_category,
    }
    res = client.post("/api/import/commit", body)
    skipped = res.get("skipped") or []
    out = [f"Booked **{res.get('booked', 0)}** of {len(chosen)} rows into {saved['accountName']}."]
    if skipped:
        out.append("Skipped: " + "; ".join(f"line {s['line']}: {s['reason']}" for s in skipped[:12]))
    return "\n".join(out)


# --------------------------------------------------------------- needs you


def needs_you(client: SumryClient, **_) -> str:
    today = dt.date.today()
    accounts = _accounts(client)
    transactions = client.get("/api/transactions/") or []
    upcoming = client.get("/api/planned/upcoming", params={"days": 1}) or []
    progress = client.get("/api/budgets/progress") or []
    items: list[str] = []

    for o in upcoming:
        day = _day(o.get("date"))
        if not o.get("overdue") and day >= today.isoformat():
            continue
        late = (today - dt.date.fromisoformat(day)).days
        items.append(
            f"- **Overdue plan** {o.get('name')} · due {day} ({late} d late) · {_signed(o.get('kind'), o.get('amount'))} "
            f"{o.get('accountName')} · plan `{str(o.get('plannedId'))[:8]}` → sumry_plan_book / sumry_plan_skip / sumry_plan_postpone"
        )
    for b in progress:
        limit = b.get("effectiveLimit") or b.get("limitAmount") or 0
        if (b.get("spentAmount") or 0) > limit:
            items.append(
                f"- **Budget over** {b.get('categoryLabel')}: {money(b.get('spentAmount'))} of {money(limit)} "
                f"({money(b['spentAmount'] - limit)} over, {b.get('daysLeft')} d left)"
            )
    loose = [t for t in transactions if t.get("kind") not in ("TRANSFER_IN", "TRANSFER_OUT") and not t.get("categoryLabel")]
    if loose:
        total = sum(abs(t.get("baseAmount") or t.get("amount") or 0) for t in loose)
        ids = ", ".join(f"`{t['id'][:8]}`" for t in loose[:10])
        items.append(f"- **{len(loose)} entries without category** ({money(total)} {CURRENCY}): {ids} → sumry_recategorise")
    with_entries = {t.get("userAccountId") for t in transactions}
    for a in accounts:
        if "lastReconciledAt" not in a:
            continue
        last = a.get("lastReconciledAt")
        if last is None:
            if a["id"] in with_entries:
                items.append(f"- **{a.get('accountName')} never checked** against the bank · Sumry shows {money(a.get('currentBalance'))} → sumry_reconcile")
            continue
        since = (today - dt.date.fromisoformat(_day(last))).days
        if since >= RECONCILE_AFTER_DAYS:
            items.append(f"- **{a.get('accountName')} not checked for {since} d** · Sumry shows {money(a.get('currentBalance'))} → sumry_reconcile")
    if today.day <= 3:
        items.append("- **Month closed**: last month's statement is ready → sumry_statement")
    if not items:
        return "Nothing needs attention right now."
    return f"## Needs you ({len(items)})\n" + "\n".join(items)


# ------------------------------------------------------------------- plans


def plan_skip(client: SumryClient, plan_id, date=None, **_) -> str:
    pid = resolve_plan_id(client, plan_id)
    params = f"?date={date}" if date else ""
    p = client.post(f"/api/planned/{pid}/skip{params}", {})
    return f"Skipped {'the occurrence on ' + date if date else 'the next occurrence'} of **{p.get('name')}**; next due {_day(p.get('nextDate'))}."


def plan_postpone(client: SumryClient, plan_id, to, date=None, **_) -> str:
    pid = resolve_plan_id(client, plan_id)
    q = f"?to={to}" + (f"&date={date}" if date else "")
    p = client.post(f"/api/planned/{pid}/postpone{q}", {})
    return f"Moved {'the ' + date if date else 'the next'} occurrence of **{p.get('name')}** to {to}."


# ------------------------------------------------------------- recategorise


def recategorise(
    client: SumryClient, category, transaction_ids=None, search=None, account=None, since=None, until=None,
    uncategorised_only=False, dry_run=None, **_
) -> str:
    if transaction_ids:
        ids = [resolve_transaction_id(client, i) for i in transaction_ids]
        targets = [t for t in (client.get("/api/transactions/") or []) if t.get("id") in set(ids)]
        dry = bool(dry_run) if dry_run is not None else False
    else:
        if not (search or uncategorised_only):
            raise SumryError("Pass transaction_ids, or a search / uncategorised_only filter.")
        acc_id = resolve_account(client, account)["id"] if account else None
        needle = (search or "").lower()
        targets = [
            t for t in (client.get("/api/transactions/") or [])
            if t.get("kind") not in ("TRANSFER_IN", "TRANSFER_OUT")
            and (not needle or needle in (t.get("description") or "").lower())
            and (not acc_id or t.get("userAccountId") == acc_id)
            and (not since or _day(t.get("date")) >= since)
            and (not until or _day(t.get("date")) <= until)
            and (not uncategorised_only or not t.get("categoryLabel"))
        ]
        # A filter can catch more than meant: preview unless told otherwise.
        dry = True if dry_run is None else bool(dry_run)
    targets = [t for t in targets if t.get("categoryLabel") != category]
    if not targets:
        return f"Nothing to change: no matching entries outside '{category}'."
    listing = table(
        ["Id", "Date", "CHF", "From", "Note"],
        [[t["id"][:8], _day(t.get("date")), money(t.get("amount")), t.get("categoryLabel") or "—", _cut(t.get("description"), 45)] for t in targets[:40]],
        {2},
    )
    more = f"\n…and {len(targets) - 40} more." if len(targets) > 40 else ""
    if dry:
        return f"Would move **{len(targets)}** entries to **{category}** (dry run, nothing changed):\n\n{listing}{more}\n\nCall again with dry_run=false to apply."
    done, failed = 0, []
    for t in targets:
        try:
            client.put(f"/api/transactions/{t['id']}", {"categoryLabel": category})
            done += 1
        except SumryError as e:
            failed.append(f"{t['id'][:8]}: {e}")
    msg = f"Moved **{done}** entries to **{category}**."
    if failed:
        msg += " Failed: " + "; ".join(failed[:5])
    return msg + f"\n\n{listing}{more}"


# ------------------------------------------------------------------- rules


def rules(
    client: SumryClient, action="list", pattern=None, category=None, match_type=None, account=None, priority=None,
    rule_id=None, text=None, dry_run=True, since=None, until=None, **_
) -> str:
    action = (action or "list").lower()
    if action == "list":
        rs = client.get("/api/rules") or []
        return table(
            ["Id", "Pattern", "Match", "Category", "Account", "Prio", "Hits", "Active"],
            [[r["id"][:8], _cut(r.get("pattern"), 30), r.get("matchType"), r.get("categoryLabel"), r.get("accountName") or "any",
              r.get("priority"), r.get("hits"), "yes" if r.get("isActive") else "no"] for r in rs],
            {5, 6},
        )
    if action == "test":
        if not text:
            raise SumryError("Pass text to test.")
        acc_id = resolve_account(client, account)["id"] if account else None
        res = client.post("/api/rules/test", {"description": text, "accountId": acc_id})
        r = res.get("rule")
        return f"'{text}' → **{res.get('categoryLabel')}** (rule `{r['id'][:8]}` {r.get('matchType')} '{r.get('pattern')}')" if r else f"'{text}' → no rule matches."
    if action == "create":
        if not (pattern and category):
            raise SumryError("Pass pattern and category.")
        body = {"pattern": pattern, "categoryLabel": category, "matchType": (match_type or "CONTAINS").upper()}
        if account:
            body["accountId"] = resolve_account(client, account)["id"]
        if priority is not None:
            body["priority"] = int(priority)
        r = client.post("/api/rules", body)
        return f"Rule `{r['id'][:8]}`: {r.get('matchType')} '{r.get('pattern')}' → **{r.get('categoryLabel')}**. Run action=apply to use it on existing entries."
    if action in ("delete", "disable", "enable"):
        rs = client.get("/api/rules") or []
        hit = [r for r in rs if r["id"].startswith((rule_id or "").strip())] if rule_id else []
        if len(hit) != 1:
            raise SumryError("Pass a rule_id (8-char id from action=list).")
        if action == "delete":
            client.delete(f"/api/rules/{hit[0]['id']}")
            return f"Deleted rule '{hit[0].get('pattern')}'."
        client.put(f"/api/rules/{hit[0]['id']}", {"isActive": action == "enable"})
        return f"Rule '{hit[0].get('pattern')}' {'enabled' if action == 'enable' else 'disabled'}."
    if action == "apply":
        q = f"?dryRun={'true' if dry_run else 'false'}" + (f"&from={since}" if since else "") + (f"&to={until}" if until else "")
        res = client.post(f"/api/rules/apply{q}", {})
        changes = res.get("changes") or []
        head = f"{'Would change' if dry_run else 'Changed'} **{res.get('changed', 0)}** of {res.get('examined')} entries."
        if isinstance(changes, list) and changes:
            head += "\n\n" + table(
                ["Id", "Date", "Note", "From", "To"],
                [[str(c.get("transactionId") or c.get("id") or "")[:8], _day(c.get("date")), _cut(c.get("description"), 40),
                  c.get("fromCategory") or c.get("from") or "—", c.get("toCategory") or c.get("to") or "—"] for c in changes[:40]],
            )
        return head + ("\n\nCall with dry_run=false to apply." if dry_run else "")
    raise SumryError("action must be list, test, create, delete, disable, enable or apply.")


# ---------------------------------------------------------------- account


def account_detail(client: SumryClient, account, **_) -> str:
    a = resolve_account(client, account)
    last = a.get("lastReconciledAt")
    since = f" ({(dt.date.today() - dt.date.fromisoformat(_day(last))).days} d ago)" if last else ""
    try:
        cf = client.get(f"/api/transactions/cashflow/{a['id']}") or {}
    except SumryError:
        cf = {}
    txs = sorted(
        (t for t in (client.get("/api/transactions/") or []) if t.get("userAccountId") == a["id"]),
        key=lambda t: t.get("date") or "", reverse=True,
    )
    month = dt.date.today().strftime("%Y-%m")
    this_month = [t for t in txs if _day(t.get("date")).startswith(month)]
    inc = sum(t.get("amount") or 0 for t in this_month if t.get("kind") in ("INCOME", "TRANSFER_IN"))
    out_ = sum(t.get("amount") or 0 for t in this_month if t.get("kind") not in ("INCOME", "TRANSFER_IN"))
    lines = [
        f"## {a.get('accountName')}",
        f"Balance **{money(a.get('currentBalance'))} {a.get('currency') or CURRENCY}** · counts toward safe-to-spend: {'yes' if a.get('spending', True) else 'no'}",
        f"Last checked against the bank: {_day(last) if last else 'never'}{since}",
        f"This month: in {money(inc)} · out {money(out_)} · net {money(inc - out_)}",
    ]
    if cf:
        lines.append(f"Cash flow (all time): in {money(cf.get('income'))} · out {money(cf.get('expenses'))}")
    lines += ["", "### Latest entries", table(
        ["Id", "Date", "CHF", "Category", "Note"],
        [[t["id"][:8], _day(t.get("date")), _signed(t.get("kind"), t.get("amount")), t.get("categoryLabel") or "—", _cut(t.get("description"), 45)] for t in txs[:12]],
        {2},
    )]
    return "\n".join(lines)


# ------------------------------------------------------------------- goals


def goals(client: SumryClient, include_inactive=False, **_) -> str:
    gs = client.get("/api/goals", params={"includeInactive": "true" if include_inactive else "false"}) or []
    if not gs:
        return "No savings goals."
    return table(
        ["Goal", "Saved", "Target", "%", "By", "Needs/month", "On track", "Account"],
        [[g.get("name"), money(g.get("current")), money(g.get("targetAmount")), f"{g.get('percentage', 0):.0f}",
          _day(g.get("targetDate")) if g.get("targetDate") else "—", money(g.get("requiredPerMonth")) if g.get("requiredPerMonth") is not None else "—",
          "achieved" if g.get("achieved") else ("yes" if g.get("onTrack") else "no" if g.get("onTrack") is False else "—"),
          g.get("accountName") or "—"] for g in gs],
        {1, 2, 3, 5},
    )


# --------------------------------------------------------------- statement


def statement(client: SumryClient, month=None, send=False, to=None, **_) -> str:
    if send:
        q = "?" + "&".join(x for x in [f"month={month}" if month else "", f"to={to}" if to else ""] if x)
        res = client.post(f"/api/statement/send{q if q != '?' else ''}", {})
        return f"Statement{' for ' + month if month else ''} emailed to {res.get('sentTo')}."
    s = client.get("/api/statement", params={"month": month} if month else None) or {}
    out = [
        f"## Statement {s.get('month')} ({s.get('from')} – {s.get('to')})",
        f"In **{money(s.get('income'))}** · out **{money(s.get('expense'))}** · net **{money(s.get('net'))}** {s.get('baseCurrency') or CURRENCY}"
        + (f" · savings rate {s['savingsRate'] * 100:.0f}%" if s.get("savingsRate") is not None else ""),
        f"Previous month: in {money(s.get('previousIncome'))} · out {money(s.get('previousExpense'))} · subscriptions {money(s.get('subscriptionsMonthly'))}/month · net worth {money(s.get('netWorth'))}",
        "",
        "### Where it went",
        table(["Category", "CHF", "Share"], [[c["label"], money(c["amount"]), f"{c['share'] * 100:.0f}%"] for c in (s.get("byCategory") or [])[:10]], {1, 2}),
    ]
    if s.get("budgets"):
        out += ["", "### Budgets", table(["Category", "Spent", "Limit", ""], [[b["category"], money(b["spent"]), money(b["limit"]), "over" if b.get("over") else ""] for b in s["budgets"]], {1, 2})]
    if s.get("largest"):
        out += ["", "### Largest", table(["Date", "CHF", "Category", "Note"], [[_day(x["date"]), money(x["amount"]), x.get("category") or "—", _cut(x.get("description"), 40)] for x in s["largest"][:8]], {1})]
    return "\n".join(out)


# ----------------------------------------------------------- subscriptions


def subscriptions(client: SumryClient, include_inactive=False, **_) -> str:
    s = client.get("/api/insights/subscriptions") or {}
    subs = [x for x in (s.get("subscriptions") or []) if include_inactive or x.get("active")]
    head = f"**{s.get('activeCount', 0)} active** · {money(s.get('monthlyTotal'))}/month · {money(s.get('yearlyTotal'))}/year\n\n"
    return head + table(
        ["Name", "Every", "CHF", "Per month", "Next", "Category", "Planned"],
        [[x.get("name"), (x.get("interval") or "").lower(), money(x.get("medianAmount")), money(x.get("monthlyEquivalent")),
          _day(x.get("nextExpected")), x.get("categoryLabel") or "—", "yes" if x.get("planned") else "no"] for x in subs],
        {2, 3},
    )
