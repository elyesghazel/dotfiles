#!/usr/bin/env python3
"""Lidl Switzerland product lookup, built on the lidl.ch storefront search API.

lidl.ch indexes every product the site shows: current and upcoming offers plus a slice of
the regular range (~700 items, ~480 of them food). The full in-store range is not published
anywhere public, so a miss here does not mean the store doesn't stock it.

    lidl.py sync [--force]            refresh the local cache (auto when older than 12h)
    lidl.py search <term>... [--all]  food matches (--all includes non-food)
                                      --all-regions keeps Tessin/Romandie-only offers
    lidl.py deals [--days N]          food offers valid now or starting within N days
    lidl.py categories                food categories with item counts
    lidl.py stores <lat> <lng> [km]   Lidl stores near a point
    lidl.py show <productId>          everything the cache has on one product

Add --json to search/deals/show for machine-readable output. Stdlib only.
"""
import html
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

CACHE = Path.home() / ".cache" / "lidl-ch" / "catalogue.json"
MAX_AGE = 12 * 3600
PAGE = 48
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
# The search API answers 401 unless the request looks like the site's own XHR.
HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-CH,de;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.lidl.ch/q/de-CH/search",
}


def get_json(url, headers=HEADERS):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_page(offset):
    qs = urllib.parse.urlencode({
        "q": "", "fetchsize": PAGE, "offset": offset,
        "locale": "de_CH", "assortment": "CH", "version": "v2.0.0",
    })
    return get_json(f"https://www.lidl.ch/q/api/search?{qs}")


def sync(force=False):
    if not force and CACHE.exists() and time.time() - CACHE.stat().st_mtime < MAX_AGE:
        return load()
    items, offset, total = [], 0, None
    while total is None or offset < total:
        d = fetch_page(offset)
        total = d.get("numFound", 0)
        page = [(i.get("gridbox") or {}).get("data") for i in d.get("items", [])]
        items += [normalize(g) for g in page if g]
        if not page:
            break
        offset += PAGE
        time.sleep(1)  # be polite: ~15 requests per full sync
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"fetchedAt": datetime.now().isoformat(timespec="seconds"),
                                 "items": items}, ensure_ascii=False))
    print(f"synced {len(items)} items ({sum(i['food'] for i in items)} food)", file=sys.stderr)
    return load()


def load():
    if not CACHE.exists():
        return sync(force=True)
    return json.loads(CACHE.read_text())


def normalize(g):
    kf = g.get("keyfacts") or {}
    facts = [html.unescape(re.sub(r"<[^>]+>", "", li)).strip()
             for li in re.findall(r"<li>(.*?)</li>", kf.get("description") or "", re.S)]
    size = next((f[4:] for f in facts if f.startswith("Pro ")), None)
    unit = next((f for f in facts if re.match(r"^[\d.,]+\s*(g|kg|ml|l|cl|dl|Stk\.?|Stück)\s*=", f)), None)
    price = g.get("price") or {}
    lp = g.get("lidlPlus") or []
    lp_price = ((lp[0] or {}).get("price") or {}).get("price") if lp else None
    windows = (g.get("stockAvailability") or {}).get("badgeInfoV2") or []
    w = windows[0] if windows else {}
    badge = " ".join(b.get("text", "") for b in w.get("badges", []))
    return {
        "id": str(g.get("productId")),
        "title": g.get("fullTitle"),
        "food": g.get("category") == "Food",
        "category": (kf.get("wonCategoryPrimary") or "").split("/")[-1],
        "price": price.get("price"),
        "oldPrice": price.get("oldPrice") or None,
        "discount": ((price.get("discount") or {}).get("discountText")) or None,
        "lidlPlusPrice": lp_price,
        "size": size,
        "unitPrice": unit,
        "facts": [f for f in facts if f not in (f"Pro {size}", unit)],
        "validFrom": w.get("validFrom"),
        "validUntil": w.get("validUntil"),
        "availability": badge or None,
        "online": bool(g.get("online")),
        "url": "https://www.lidl.ch" + (g.get("canonicalUrl") or ""),
    }


# Offers flagged for another region don't apply in St. Gallen (Deutschschweiz).
OTHER_REGION = re.compile(r"\(Aktion nur (im Tessin|in der Westschweiz|in der Westschweiz und im Tessin)( gültig)?\)")


def km_between(a_lat, a_lng, b_lat, b_lng):
    p = math.pi / 180
    h = (math.sin((b_lat - a_lat) * p / 2) ** 2
         + math.cos(a_lat * p) * math.cos(b_lat * p) * math.sin((b_lng - a_lng) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(h))


def fmt_date(ts):
    return datetime.fromtimestamp(ts).strftime("%a %d.%m.") if ts else ""


def line(i):
    p = f"CHF {i['price']:.2f}" if i["price"] is not None else "CHF ?"
    if i["oldPrice"]:
        p += f" (statt {i['oldPrice']:.2f})"
    if i["lidlPlusPrice"]:
        p += f" / Lidl Plus {i['lidlPlusPrice']:.2f}"
    size = " · ".join(x for x in (i["size"], i["unitPrice"]) if x)
    when = i["availability"] or ""
    return f"{i['title']}  |  {p}  |  {size or '-'}  |  {i['category']}  |  {when}  [{i['id']}]"


def matches(item, terms):
    hay = f"{item['title']} {item['category']} {' '.join(item['facts'])}".lower()
    return all(t.lower() in hay for t in terms)


def main(argv):
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]

    if cmd == "sync":
        sync(force="--force" in args)
        return

    if cmd == "stores":
        lat, lng = args[0], args[1]
        km = float(args[2]) if len(args) > 2 else 5
        qs = urllib.parse.urlencode({"countryCode": "CH", "latitude": lat, "longitude": lng,
                                     "radius": int(km * 1000)})
        stores = get_json(f"https://stores.lidlplus.com/api/v2/CH?{qs}", {"User-Agent": UA})
        near = []
        for s in stores if isinstance(stores, list) else []:
            loc = s.get("location") or {}
            d = km_between(float(lat), float(lng), loc.get("latitude", 0), loc.get("longitude", 0))
            if d <= km:
                near.append((d, s))
        for d, s in sorted(near, key=lambda x: x[0]):
            print(f"{s.get('storeKey')}  {d:4.1f} km  {s.get('address')}, {s.get('postalCode')} {s.get('locality')}")
        return

    data = sync()
    items = data["items"]
    if "--all-regions" not in args:
        items = [i for i in items if not OTHER_REGION.search(i["title"] or "")]

    if cmd == "search":
        include_all = "--all" in args
        terms = [a for a in args if not a.startswith("--")]
        hits = [i for i in items if (include_all or i["food"]) and matches(i, terms)]
        hits.sort(key=lambda i: (i["price"] is None, i["price"] or 0))
    elif cmd == "deals":
        days = int(args[args.index("--days") + 1]) if "--days" in args else 7
        horizon = (datetime.now() + timedelta(days=days)).timestamp()
        now = time.time()
        # A deal = reduced price, a Lidl Plus price, or a dated offer window with an end.
        hits = [i for i in items if i["food"] and i["validFrom"]
                and (i["oldPrice"] or i["lidlPlusPrice"] or i["validUntil"])
                and i["validFrom"] <= horizon and (i["validUntil"] or now) >= now]
        hits.sort(key=lambda i: (i["category"], i["title"]))
    elif cmd == "categories":
        from collections import Counter
        for cat, n in Counter(i["category"] for i in items if i["food"]).most_common():
            print(f"{n:4}  {cat}")
        return
    elif cmd == "show":
        hits = [i for i in items if i["id"] == args[0]]
    else:
        sys.exit(f"unknown command: {cmd}\n{__doc__}")

    if as_json:
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return
    print(f"# {len(hits)} result(s) - cache from {data['fetchedAt']}")
    for i in hits:
        print(line(i))
        if cmd == "show":
            print(json.dumps(i, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
