"""Tool implementations for the Sumry MCP server.

Every tool returns Markdown rather than raw JSON: the model reads these directly,
and a rendered table costs far fewer tokens than the API's UUID-heavy payloads.
Account ids are resolved from names so callers can say "PostFinance" instead of
carrying a UUID around.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from client import SumryClient, SumryError

CURRENCY = "CHF"


# --------------------------------------------------------------- formatting


def money(value) -> str:
    if value is None:
        return "—"
    return f"{value:,.2f}".replace(",", "'")


def _day(value) -> str:
    if not value:
        return "—"
    text = str(value)
    # The API hands back ISO-8601; everything after the date is noise here.
    return text[:10]


def table(headers: list[str], rows: list[list[str]], align_right: set[int] | None = None) -> str:
    if not rows:
        return "_No rows._"
    align_right = align_right or set()
    sep = ["---:" if i in align_right else "---" for i in range(len(headers))]
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


# ------------------------------------------------------------------ helpers


def resolve_transaction_id(client: SumryClient, ref: str) -> str:
    """Accept a full UUID or the 8-char prefix the transactions table prints."""
    needle = (ref or "").strip().lower()
    if not needle:
        raise SumryError("No transaction id given.")
    if len(needle) >= 32:
        return needle
    matches = [t["id"] for t in (client.get("/api/transactions/") or []) if str(t.get("id", "")).lower().startswith(needle)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SumryError(f"No transaction starts with `{ref}`.")
    raise SumryError(f"`{ref}` matches {len(matches)} transactions — pass more characters.")


def _accounts(client: SumryClient) -> list[dict]:
    return client.get("/api/users/accounts/") or []


def resolve_account(client: SumryClient, name_or_id: str) -> dict:
    """Accept a UUID, an exact name, or an unambiguous case-insensitive prefix."""
    accounts = _accounts(client)
    needle = (name_or_id or "").strip()
    if not needle:
        raise SumryError("No account given.")

    for account in accounts:
        if account.get("id") == needle:
            return account

    lowered = needle.lower()
    exact = [a for a in accounts if (a.get("accountName") or "").lower() == lowered]
    if len(exact) == 1:
        return exact[0]

    partial = [a for a in accounts if lowered in (a.get("accountName") or "").lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        names = ", ".join(a.get("accountName") or "?" for a in partial)
        raise SumryError(f"'{needle}' matches several accounts: {names}.")

    known = ", ".join(a.get("accountName") or "?" for a in accounts)
    raise SumryError(f"No account matching '{needle}'. Known accounts: {known}.")


def _account_names(client: SumryClient) -> dict[str, str]:
    return {a["id"]: a.get("accountName") or "?" for a in _accounts(client) if a.get("id")}


def _iso(value: str | None) -> str:
    """Normalise a date the model supplies into what Jackson expects."""
    if not value:
        return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    text = value.strip()
    if len(text) == 10:  # bare YYYY-MM-DD — pin it to midday, not midnight,
        return f"{text}T12:00:00"  # so a timezone shift cannot move the day
    return text.replace("Z", "")


def _in_window(transaction: dict, since: str | None, until: str | None) -> bool:
    day = _day(transaction.get("date"))
    if since and day < since:
        return False
    if until and day > until:
        return False
    return True


def _month_bounds(month: str | None) -> tuple[str, str, str]:
    today = dt.date.today()
    if month:
        year, mon = int(month[:4]), int(month[5:7])
    else:
        year, mon = today.year, today.month
    first = dt.date(year, mon, 1)
    last = dt.date(year + (mon == 12), (mon % 12) + 1, 1) - dt.timedelta(days=1)
    return first.isoformat(), last.isoformat(), f"{year:04d}-{mon:02d}"


# -------------------------------------------------------------------- tools


def list_accounts(client: SumryClient, **_) -> str:
    accounts = sorted(
        _accounts(client), key=lambda a: a.get("currentBalance") or 0, reverse=True
    )
    rows = [[a.get("accountName") or "?", money(a.get("currentBalance"))] for a in accounts]
    total = sum(a.get("currentBalance") or 0 for a in accounts)
    body = table(["Account", f"Balance ({CURRENCY})"], rows, align_right={1})
    return f"{body}\n\n**Total: {money(total)} {CURRENCY}** across {len(accounts)} accounts."


def list_transactions(
    client: SumryClient,
    account=None,
    since=None,
    until=None,
    category=None,
    kind=None,
    search=None,
    limit=25,
    **_,
) -> str:
    transactions = client.get("/api/transactions/") or []
    names = _account_names(client)

    if account:
        wanted = resolve_account(client, account)["id"]
        transactions = [t for t in transactions if t.get("userAccountId") == wanted]
    if kind:
        wanted_kinds = {k.strip().upper() for k in kind.split(",")}
        transactions = [t for t in transactions if (t.get("kind") or "") in wanted_kinds]
    if category:
        needle = category.lower()
        transactions = [t for t in transactions if needle in (t.get("categoryLabel") or "").lower()]
    if search:
        needle = search.lower()
        transactions = [t for t in transactions if needle in (t.get("description") or "").lower()]
    transactions = [t for t in transactions if _in_window(t, since, until)]

    transactions.sort(key=lambda t: str(t.get("date") or ""), reverse=True)
    shown = transactions[: max(1, int(limit))]

    rows = []
    for t in shown:
        amount = t.get("amount") or 0
        sign = "−" if (t.get("kind") or "").startswith(("EXPENSE", "TRANSFER_OUT")) else "+"
        rows.append(
            [
                _day(t.get("date")),
                f"{sign}{money(amount)}",
                t.get("categoryLabel") or (t.get("kind") or "").replace("_", " ").title(),
                (t.get("description") or "").strip() or "—",
                names.get(t.get("userAccountId"), "?"),
                (t.get("id") or "")[:8],
            ]
        )

    header = table(
        ["Date", CURRENCY, "Category", "Description", "Account", "Id"], rows, align_right={1}
    )
    note = f"\n\nShowing {len(shown)} of {len(transactions)} matching."
    return header + note


def summary(client: SumryClient, month=None, **_) -> str:
    since, until, label = _month_bounds(month)
    transactions = [t for t in (client.get("/api/transactions/") or []) if _in_window(t, since, until)]
    accounts = _accounts(client)

    income = sum(t.get("amount") or 0 for t in transactions if t.get("kind") == "INCOME")
    expense = sum(t.get("amount") or 0 for t in transactions if t.get("kind") == "EXPENSE")
    net = income - expense

    by_category: dict[str, float] = defaultdict(float)
    for t in transactions:
        if t.get("kind") == "EXPENSE":
            by_category[t.get("categoryLabel") or "(uncategorised)"] += t.get("amount") or 0
    top = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)[:8]

    total = sum(a.get("currentBalance") or 0 for a in accounts)
    balances = table(
        ["Account", CURRENCY],
        [
            [a.get("accountName") or "?", money(a.get("currentBalance"))]
            for a in sorted(accounts, key=lambda a: a.get("currentBalance") or 0, reverse=True)
        ],
        align_right={1},
    )
    spending = table(
        ["Category", CURRENCY, "Share"],
        [[name, money(amount), f"{amount / expense * 100:.0f}%" if expense else "—"] for name, amount in top],
        align_right={1, 2},
    )

    return (
        f"## Sumry — {label}\n\n"
        f"**Net worth {money(total)} {CURRENCY}**\n\n"
        f"{balances}\n\n"
        f"### Cashflow\n\n"
        f"| | {CURRENCY} |\n| --- | ---: |\n"
        f"| Income | {money(income)} |\n"
        f"| Expenses | {money(expense)} |\n"
        f"| **Net** | **{'+' if net >= 0 else '−'}{money(abs(net))}** |\n\n"
        f"### Top spending\n\n{spending}\n\n"
        f"_{len(transactions)} transactions between {since} and {until}._"
    )


def monthly_trend(client: SumryClient, months=6, **_) -> str:
    transactions = client.get("/api/transactions/") or []
    buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"INCOME": 0.0, "EXPENSE": 0.0})
    for t in transactions:
        kind = t.get("kind")
        if kind in ("INCOME", "EXPENSE"):
            buckets[_day(t.get("date"))[:7]][kind] += t.get("amount") or 0

    ordered = sorted(buckets.items(), reverse=True)[: max(1, int(months))]
    rows = [
        [
            month,
            money(v["INCOME"]),
            money(v["EXPENSE"]),
            f"{'+' if v['INCOME'] - v['EXPENSE'] >= 0 else '−'}{money(abs(v['INCOME'] - v['EXPENSE']))}",
        ]
        for month, v in ordered
    ]
    return table(["Month", "Income", "Expenses", "Net"], rows, align_right={1, 2, 3})


def list_categories(client: SumryClient, kind=None, include_inactive=False, **_) -> str:
    categories = client.get("/api/category/user") or []
    if not include_inactive:
        categories = [c for c in categories if c.get("isActive")]
    if kind:
        categories = [c for c in categories if (c.get("categoryType") or "") == kind.upper()]

    rows = [
        [c.get("label") or "?", c.get("categoryType") or "?", c.get("parentGroup") or "—"]
        for c in sorted(categories, key=lambda c: ((c.get("categoryType") or ""), c.get("label") or ""))
    ]
    return table(["Label", "Type", "Group"], rows)


def log_transaction(
    client: SumryClient, amount, category, account, description=None, date=None, **_
) -> str:
    target = resolve_account(client, account)
    created = client.post(
        "/api/transactions/",
        {
            "amount": abs(float(amount)),
            "description": description,
            "categoryLabel": category,
            "date": _iso(date),
            "userAccountId": target["id"],
        },
    )
    kind = (created or {}).get("kind", "?")
    return (
        f"Logged **{money(created.get('amount'))} {CURRENCY}** ({kind}) "
        f"as _{created.get('categoryLabel')}_ on **{target['accountName']}** "
        f"({_day(created.get('date'))}).\n\n"
        f"Balance {money(created.get('balanceBefore'))} → **{money(created.get('balanceAfter'))} {CURRENCY}**."
    )


def transfer(client: SumryClient, amount, from_account, to_account, description=None, date=None, **_) -> str:
    source = resolve_account(client, from_account)
    dest = resolve_account(client, to_account)
    if source["id"] == dest["id"]:
        raise SumryError("Source and destination are the same account.")
    client.post(
        "/api/transactions/transfer",
        {
            "amount": abs(float(amount)),
            "description": description,
            "fromAccountId": source["id"],
            "toAccountId": dest["id"],
            "date": _iso(date),
        },
    )
    return (
        f"Transferred **{money(abs(float(amount)))} {CURRENCY}** "
        f"from **{source['accountName']}** to **{dest['accountName']}**."
    )


def reconcile(client: SumryClient, account, new_balance, note=None, **_) -> str:
    target = resolve_account(client, account)
    before = target.get("currentBalance") or 0
    result = client.put(
        f"/api/users/accounts/reconcile/{target['id']}",
        {"newBalance": float(new_balance), "note": note},
    )
    if result is None:
        return f"**{target['accountName']}** already reads {money(before)} {CURRENCY} — nothing booked."
    delta = float(new_balance) - before
    return (
        f"**{target['accountName']}** {money(before)} → **{money(new_balance)} {CURRENCY}**.\n\n"
        f"Booked a {money(abs(delta))} {CURRENCY} {result.get('kind')} adjustment "
        f"(_{result.get('categoryLabel')}_, \"{result.get('description')}\") so history still adds up."
    )


def update_transaction(
    client: SumryClient, transaction_id, amount=None, description=None, category=None, date=None, account=None, **_
) -> str:
    payload = {}
    if amount is not None:
        payload["amount"] = abs(float(amount))
    if description is not None:
        payload["description"] = description
    if category is not None:
        payload["categoryLabel"] = category
    if date is not None:
        payload["date"] = _iso(date)
    if account is not None:
        payload["userAccountId"] = resolve_account(client, account)["id"]
    if not payload:
        raise SumryError("Nothing to update — pass at least one field.")

    transaction_id = resolve_transaction_id(client, transaction_id)
    updated = client.put(f"/api/transactions/{transaction_id}", payload)
    return (
        f"Updated transaction `{transaction_id[:8]}`: "
        f"{money(updated.get('amount'))} {CURRENCY} _{updated.get('categoryLabel')}_ "
        f"({_day(updated.get('date'))}). New balance {money(updated.get('balanceAfter'))} {CURRENCY}."
    )


def delete_transaction(client: SumryClient, transaction_id, **_) -> str:
    transaction_id = resolve_transaction_id(client, transaction_id)
    client.delete(f"/api/transactions/{transaction_id}")
    return f"Deleted transaction `{transaction_id[:8]}`; the account balance was reverted."


def list_budgets(client: SumryClient, month=None, **_) -> str:
    _, _, label = _month_bounds(month)
    year, mon = int(label[:4]), int(label[5:7])
    progress = client.get("/api/budgets/progress", params={"month": mon, "year": year}) or []
    if not progress:
        return "No budgets set."
    rows = [
        [
            p.get("categoryLabel") or "?",
            money(p.get("spentAmount")),
            money(p.get("limitAmount")),
            money(p.get("remaining")),
            f"{p.get('percentage') or 0:.0f}%",
        ]
        for p in progress
    ]
    body = table(["Category", "Spent", "Limit", "Left", "Used"], rows, align_right={1, 2, 3, 4})
    return f"## Budgets — {label}\n\n{body}"


def create_account(client: SumryClient, name, starting_balance=0.0, **_) -> str:
    created = client.post(
        "/api/users/accounts",
        {"accountName": name, "currentBalance": float(starting_balance)},
    )
    return f"Created **{created.get('accountName')}** at {money(created.get('currentBalance'))} {CURRENCY}."


# ------------------------------------------------------------ planned

_FREQUENCIES = {"DAILY", "WEEKLY", "MONTHLY", "YEARLY", "ONCE"}


def _signed(kind: str | None, amount) -> str:
    sign = "−" if (kind or "").startswith(("EXPENSE", "TRANSFER_OUT")) else "+"
    return f"{sign}{money(amount)}"


def _plan_target(p: dict) -> str:
    """Category for an income/expense plan, 'A → B' for a planned transfer."""
    if p.get("toAccountName"):
        return f"→ {p['toAccountName']}"
    return p.get("categoryLabel") or "—"


def _frequency(value: str | None) -> str | None:
    if value is None:
        return None
    freq = value.strip().upper()
    if freq not in _FREQUENCIES:
        raise SumryError(f"Unknown frequency '{value}'. Use one of: {', '.join(sorted(_FREQUENCIES))}.")
    return freq


def _date_only(value: str | None) -> str | None:
    # Plans take a LocalDate, so anything past the day would fail Jackson.
    return value.strip()[:10] if value else None


def resolve_plan_id(client: SumryClient, ref: str) -> str:
    """Accept a full UUID, the 8-char prefix the plans table prints, or a plan name."""
    needle = (ref or "").strip().lower()
    if not needle:
        raise SumryError("No plan id given.")
    if len(needle) >= 32:
        return needle
    plans = client.get("/api/planned", params={"includeInactive": "true"}) or []
    matches = [p for p in plans if str(p.get("id", "")).lower().startswith(needle)]
    if not matches:
        exact = [p for p in plans if (p.get("name") or "").lower() == needle]
        matches = exact or [p for p in plans if needle in (p.get("name") or "").lower()]
    if len(matches) == 1:
        return matches[0]["id"]
    if not matches:
        raise SumryError(f"No plan matches `{ref}`.")
    names = ", ".join(f"{p.get('name')} ({p['id'][:8]})" for p in matches)
    raise SumryError(f"`{ref}` matches several plans: {names}.")


def list_planned(client: SumryClient, include_inactive=False, **_) -> str:
    plans = client.get("/api/planned", params={"includeInactive": str(bool(include_inactive)).lower()}) or []
    if not plans:
        return "No planned transactions."
    plans.sort(key=lambda p: (p.get("nextDate") or "9999", p.get("name") or ""))

    rows = []
    for p in plans:
        flags = []
        if p.get("autoBook"):
            flags.append("auto")
        if not p.get("isActive"):
            flags.append("paused")
        rows.append(
            [
                p.get("name") or "?",
                _signed(p.get("kind"), p.get("amount")),
                (p.get("frequency") or "?").lower(),
                p.get("nextDate") or "—",
                _plan_target(p),
                p.get("accountName") or "?",
                money(p.get("monthlyEquivalent")),
                ", ".join(flags) or "—",
                (p.get("id") or "")[:8],
            ]
        )
    body = table(
        ["Plan", CURRENCY, "Every", "Next", "Category", "Account", "Per month", "Flags", "Id"],
        rows,
        align_right={1, 6},
    )

    active = [p for p in plans if p.get("isActive")]
    monthly_in = sum(p.get("monthlyEquivalent") or 0 for p in active if p.get("kind") == "INCOME")
    monthly_out = sum(p.get("monthlyEquivalent") or 0 for p in active if p.get("kind") == "EXPENSE")
    return (
        f"{body}\n\n"
        f"Active plans per month: **+{money(monthly_in)}** in, **−{money(monthly_out)}** out "
        f"(transfers excluded). `auto` plans book themselves when due."
    )


def upcoming_planned(client: SumryClient, days=30, account=None, **_) -> str:
    params = {"days": max(1, min(366, int(days)))}
    if account:
        params["accountId"] = resolve_account(client, account)["id"]
    occurrences = client.get("/api/planned/upcoming", params=params) or []
    if not occurrences:
        return f"Nothing planned in the next {params['days']} days."

    rows = [
        [
            o.get("date") or "?",
            _signed(o.get("kind"), o.get("amount")),
            o.get("name") or "?",
            _plan_target(o),
            o.get("accountName") or "?",
            "**overdue**" if o.get("overdue") else ("auto" if o.get("autoBook") else "manual"),
            (o.get("plannedId") or "")[:8],
        ]
        for o in occurrences
    ]
    body = table(["Date", CURRENCY, "Plan", "Category", "Account", "Booking", "Plan id"], rows, align_right={1})
    income = sum(o.get("amount") or 0 for o in occurrences if o.get("kind") == "INCOME")
    expense = sum(o.get("amount") or 0 for o in occurrences if o.get("kind") == "EXPENSE")
    overdue = sum(1 for o in occurrences if o.get("overdue"))
    note = f"\n\nNext {params['days']} days: +{money(income)} in, −{money(expense)} out."
    if overdue:
        note += f" **{overdue} overdue** — due but never booked; `sumry_plan_book` books them."
    return body + note


def safe_to_spend(client: SumryClient, account=None, **_) -> str:
    target = resolve_account(client, account) if account else None
    params = {"accountId": target["id"]} if target else None
    s = client.get("/api/planned/safe-to-spend", params=params) or {}
    scope = f"**{target['accountName']}**" if target else "all accounts"
    committed = (s.get("upcomingExpenses") or 0) + (s.get("upcomingTransfersOut") or 0)
    lines = [
        f"## Safe to spend: {money(s.get('safeToSpend'))} {CURRENCY}",
        "",
        f"≈ **{money(s.get('perDay'))} {CURRENCY}/day** for {s.get('daysToHorizon')} days "
        f"until {s.get('horizon')} ({s.get('horizonReason')}).",
        "",
        "| | " + CURRENCY + " |",
        "| --- | ---: |",
        f"| Balance ({scope}) | {money(s.get('balance'))} |",
        f"| Planned expenses | −{money(s.get('upcomingExpenses'))} |",
    ]
    if s.get("upcomingTransfersOut"):
        lines.append(f"| Planned transfers out | −{money(s.get('upcomingTransfersOut'))} |")
    lines.append(f"| **Safe to spend** | **{money(s.get('safeToSpend'))}** |")

    upcoming = s.get("upcoming") or []
    if upcoming and committed:
        lines += ["", "Committed before then:", ""]
        lines.append(
            table(
                ["Date", CURRENCY, "Plan"],
                [
                    [o.get("date"), _signed(o.get("kind"), o.get("amount")), o.get("name") or "?"]
                    for o in upcoming
                    if o.get("kind") != "INCOME"
                ],
                align_right={1},
            )
        )
    return "\n".join(lines)


def create_plan(
    client: SumryClient,
    name,
    amount,
    frequency,
    start_date,
    account,
    category=None,
    to_account=None,
    end_date=None,
    description=None,
    auto_book=False,
    **_,
) -> str:
    if not category and not to_account:
        raise SumryError("Pass a category (income/expense) or to_account (transfer).")
    source = resolve_account(client, account)
    payload = {
        "name": name,
        "amount": abs(float(amount)),
        "description": description,
        "startDate": _date_only(start_date),
        "endDate": _date_only(end_date),
        "frequency": _frequency(frequency),
        "accountId": source["id"],
        "autoBook": bool(auto_book),
    }
    if to_account:
        payload["toAccountId"] = resolve_account(client, to_account)["id"]
    else:
        payload["categoryLabel"] = category
    p = client.post("/api/planned", payload)
    return (
        f"Planned **{p.get('name')}**: {_signed(p.get('kind'), p.get('amount'))} {CURRENCY} "
        f"{(p.get('frequency') or '').lower()}, {_plan_target(p)} on **{p.get('accountName')}**. "
        f"Next {p.get('nextDate') or '—'}, "
        f"{'books itself' if p.get('autoBook') else 'reminder only'}. Id `{(p.get('id') or '')[:8]}`."
    )


def update_plan(
    client: SumryClient,
    plan_id,
    name=None,
    amount=None,
    frequency=None,
    start_date=None,
    end_date=None,
    account=None,
    category=None,
    to_account=None,
    description=None,
    auto_book=None,
    active=None,
    **_,
) -> str:
    payload = {}
    if name is not None:
        payload["name"] = name
    if amount is not None:
        payload["amount"] = abs(float(amount))
    if frequency is not None:
        payload["frequency"] = _frequency(frequency)
    if start_date is not None:
        payload["startDate"] = _date_only(start_date)
    if end_date is not None:
        # An empty string means "runs forever" — the API needs an explicit flag for that.
        if end_date.strip():
            payload["endDate"] = _date_only(end_date)
        else:
            payload["clearEndDate"] = True
    if account is not None:
        payload["accountId"] = resolve_account(client, account)["id"]
    if category is not None:
        payload["categoryLabel"] = category
    if to_account is not None:
        payload["toAccountId"] = resolve_account(client, to_account)["id"]
    if description is not None:
        payload["description"] = description
    if auto_book is not None:
        payload["autoBook"] = bool(auto_book)
    if active is not None:
        payload["isActive"] = bool(active)
    if not payload:
        raise SumryError("Nothing to update — pass at least one field.")

    plan_id = resolve_plan_id(client, plan_id)
    p = client.put(f"/api/planned/{plan_id}", payload)
    state = "active" if p.get("isActive") else "paused"
    return (
        f"Updated plan **{p.get('name')}** (`{plan_id[:8]}`): "
        f"{_signed(p.get('kind'), p.get('amount'))} {CURRENCY} {(p.get('frequency') or '').lower()}, "
        f"{_plan_target(p)} on {p.get('accountName')}, next {p.get('nextDate') or '—'}, {state}."
    )


def delete_plan(client: SumryClient, plan_id, **_) -> str:
    plan_id = resolve_plan_id(client, plan_id)
    client.delete(f"/api/planned/{plan_id}")
    return f"Deleted plan `{plan_id[:8]}`. Occurrences already booked stay in the history."


def book_plan(client: SumryClient, plan_id, date=None, **_) -> str:
    plan_id = resolve_plan_id(client, plan_id)
    path = f"/api/planned/{plan_id}/book"
    if date:
        path += f"?date={_date_only(date)}"
    p = client.post(path)
    return (
        f"Booked **{p.get('name')}** ({_signed(p.get('kind'), p.get('amount'))} {CURRENCY}) "
        f"on {p.get('accountName')}. Next occurrence {p.get('nextDate') or '— (plan finished)'}."
    )
