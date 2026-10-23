---
name: lidl
description: Look up Lidl Switzerland products, prices, pack sizes, unit prices (CHF/kg), Lidl Plus prices and offer dates from the lidl.ch catalogue. Use whenever the user asks what Lidl has or costs, wants to compare a Migros/Coop item against Lidl, plans a shopping list or meal plan that should include Lidl, asks about Lidl deals/Aktionen this week or next, or mentions their Lidl store (St. Gallen Rorschacher Strasse 154, CH0388).
---

# Lidl (Switzerland)

`scripts/lidl.py` pulls the whole lidl.ch product index (the API behind the site's search box)
into `~/.cache/lidl-ch/catalogue.json` and searches it locally. Stdlib Python, no install.

```bash
S=~/.claude/skills/lidl/scripts/lidl.py
python3 $S search poulet            # food matches, cheapest first
python3 $S search spaghetti --json  # machine-readable
python3 $S deals --days 7           # food offers live now or starting within 7 days
python3 $S categories               # what food categories exist and how many items
python3 $S show 10060304            # one product, all fields
python3 $S stores 47.43 9.39 3      # stores near a point (lat lng km)
python3 $S sync --force             # refresh now (otherwise auto after 12h)
```

Output per line: title | price (old price, Lidl Plus price) | pack size · unit price |
category | in-store dates | [productId].

## What the data covers - say this when it matters

lidl.ch indexes **~700 products (~480 food)**: the current and next week's offers plus a slice
of the regular range (e.g. COMBINO pasta, GOLDEN SUN rice, MILBONA dairy). The full in-store
range (well over 1,000 food items) is **not published anywhere public**. So:

- A hit is a real Lidl price for Switzerland, with pack size and validity dates.
- A miss does **not** mean the store lacks it. Plain eggs, bananas or Magerquark are usually
  in the store but missing from the index. Say "not in Lidl's online catalogue - check in
  store" instead of "Lidl doesn't have it".
- Prices are national. Dates in the `availability` column are offer windows
  ("15.10. - 17.10." = Thu-Sat); items without dates are listed without a window.
- "Pro 100 g" with "Ca. 300-800 g" means a per-100g price on a variable-weight pack.

## Elyes' store

**Lidl St. Gallen, Rorschacher Strasse 154 (Shopping Silberturm), store `CH0388`.**
Migros Silberturm is next door (Rorschacher Strasse 150), so a split Lidl + Migros shop is
one trip. For Migros prices use the `migros` MCP; for Coop/Aldi/Denner the `swissgroceries`
MCP.

## Comparing with Migros

Compare on unit price (CHF/kg or per 100 g), not pack price. When building a shopping list,
take each item from whichever store is cheaper per kg, and mark Lidl-only offers with their
date window so the shop happens inside it.
