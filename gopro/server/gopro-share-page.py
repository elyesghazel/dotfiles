#!/usr/bin/env python3
"""Render a gopro-share collection dashboard from its .meta.json.

Self-contained: no CDN, no fonts, no build step — nginx just serves the file.
Download links go through /dl/ (nginx adds Content-Disposition there); the plain
paths stay inline so <video> can stream and seek via range requests.
"""
import json, sys, html

meta = json.load(open(sys.argv[1]))
items, expires, title = meta["items"], meta["expires"], meta["title"]


def human(n):
    if not n:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024


def label(h):
    """Human name for a video height: the picker says 4K, not 2160p."""
    h = int(h or 0)
    if h >= 2100:
        return "4K"
    if h >= 1400:
        return "1440p"
    if h >= 1000:
        return "1080p"
    return f"{h}p" if h else "original"


def clock(sec):
    sec = int(sec or 0)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


total = sum(i["size"] for i in items)
cards = []
for i in items:
    f = html.escape(i["file"])
    stem = html.escape(i["file"].rsplit(".", 1)[0])
    thumb = html.escape(i["thumb"])
    poster = f'<img src="t/{thumb}" alt="" loading="lazy">' if thumb else '<div class="noposter"></div>'
    res = f'{i["w"]}×{i["h"]}' if i["w"] else ""
    meta_line = " · ".join(x for x in (res, human(i["size"])) if x)
    # Quality picker: the stream copy is always there, the original only when the
    # share staged one. Label the original by its real height (4K / 5.3K / 2.7K …)
    # rather than assuming — GoPro modes vary and the archive is whatever was shot.
    qs = [f'<a class="q" href="dl/v/{f}"><b>{label(i["h"])}</b><span>{human(i["size"])}</span></a>']
    if i.get("orig"):
        o = html.escape(i["orig"])
        qs.append(f'<a class="q q-hi" href="dl/4k/{o}"><b>{label(i.get("origH") or 2160)}</b>'
                  f'<span>{human(i["origSize"])}</span></a>')
    dl = [f'<p class="dlab">Download</p><div class="qs">{"".join(qs)}</div>']
    cards.append(f'''    <article class="card">
      <button class="poster" data-src="v/{f}" data-name="{stem}" aria-label="Play {stem}">
        {poster}
        <span class="play" aria-hidden="true"></span>
        <span class="dur">{clock(i["dur"])}</span>
      </button>
      <div class="body">
        <h2 title="{f}">{stem}</h2>
        <p class="meta">{meta_line}</p>
        <div class="dl">{"".join(dl)}</div>
      </div>
    </article>''')

print(f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(title)} — shared clips</title>
<style>
  :root {{
    --bg:#0f1115; --panel:#171a21; --panel-2:#1e222b; --line:#272c37;
    --fg:#e8eaf0; --muted:#8b93a7; --accent:#4f9cf9; --accent-fg:#04101f;
    --radius:14px;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg:#f4f6fa; --panel:#fff; --panel-2:#eef1f7; --line:#dfe4ee;
      --fg:#141822; --muted:#5f6980; --accent:#1f6feb; --accent-fg:#fff;
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--fg); -webkit-font-smoothing:antialiased;
    font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:40px 20px 72px; }}
  header {{ margin-bottom:28px; }}
  h1 {{ margin:0 0 6px; font-size:26px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); font-size:14px; margin:0; }}
  .sub b {{ color:var(--fg); font-weight:600; }}
  #exp.soon {{ color:#f0883e; }}
  .grid {{
    display:grid; gap:18px; grid-template-columns:repeat(auto-fill,minmax(275px,1fr));
  }}
  .card {{
    background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
    overflow:hidden; display:flex; flex-direction:column;
  }}
  .poster {{
    all:unset; position:relative; display:block; cursor:pointer; aspect-ratio:16/9;
    background:#000; overflow:hidden;
  }}
  .poster img {{ width:100%; height:100%; object-fit:cover; display:block; transition:transform .25s ease; }}
  .poster:hover img {{ transform:scale(1.04); }}
  .poster:focus-visible {{ outline:2px solid var(--accent); outline-offset:-2px; }}
  .noposter {{ width:100%; height:100%; background:linear-gradient(135deg,#222835,#141821); }}
  .play {{
    position:absolute; inset:0; margin:auto; width:52px; height:52px; border-radius:50%;
    background:rgba(10,12,18,.62); backdrop-filter:blur(2px);
    border:1px solid rgba(255,255,255,.22);
  }}
  .play::after {{
    content:""; position:absolute; inset:0; margin:auto; width:0; height:0;
    border-style:solid; border-width:9px 0 9px 15px; border-color:transparent transparent transparent #fff;
    transform:translateX(2px);
  }}
  .dur {{
    position:absolute; right:8px; bottom:8px; padding:2px 6px; border-radius:6px;
    background:rgba(10,12,18,.78); color:#fff; font-size:12px; font-variant-numeric:tabular-nums;
  }}
  .body {{ padding:12px 14px 14px; display:flex; flex-direction:column; gap:10px; flex:1; }}
  h2 {{
    margin:0; font-size:14.5px; font-weight:600; letter-spacing:-.01em;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  }}
  .meta {{ margin:0; color:var(--muted); font-size:12.5px; }}
  .dl {{ margin-top:auto; }}
  .dlab {{
    margin:0 0 5px; font-size:11px; font-weight:600; letter-spacing:.07em;
    text-transform:uppercase; color:var(--muted);
  }}
  .qs {{ display:flex; gap:6px; }}
  .q {{
    flex:1; display:flex; flex-direction:column; align-items:center; gap:1px;
    padding:8px 6px; border-radius:9px; text-decoration:none;
    background:var(--panel-2); color:var(--fg); border:1px solid var(--line);
    transition:background .15s ease, border-color .15s ease;
  }}
  .q b {{ font-size:13px; font-weight:650; letter-spacing:-.01em; }}
  .q span {{ font-size:11.5px; color:var(--muted); font-variant-numeric:tabular-nums; }}
  .q:hover {{ background:var(--accent); border-color:var(--accent); color:var(--accent-fg); }}
  .q:hover span {{ color:inherit; opacity:.8; }}
  .q-hi {{ border-color:color-mix(in srgb, var(--accent) 45%, var(--line)); }}
  dialog {{
    padding:0; border:none; background:transparent; max-width:min(1100px,94vw); width:100%;
  }}
  dialog::backdrop {{ background:rgba(6,8,12,.86); }}
  dialog video {{ width:100%; display:block; border-radius:12px; background:#000; }}
  .dlgbar {{
    display:flex; justify-content:space-between; align-items:center; gap:12px;
    color:#e8eaf0; font-size:14px; padding:0 2px 10px;
  }}
  .dlgbar button {{
    all:unset; cursor:pointer; padding:5px 12px; border-radius:8px;
    background:rgba(255,255,255,.12); font-size:13px; font-weight:600;
  }}
  .dlgbar button:hover {{ background:rgba(255,255,255,.2); }}
  footer {{ margin-top:36px; color:var(--muted); font-size:12.5px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{html.escape(title)}</h1>
    <p class="sub"><b>{len(items)}</b> clip{"s" if len(items) != 1 else ""} · <b>{human(total)}</b> · link expires <b id="exp">…</b></p>
  </header>
  <div class="grid">
{chr(10).join(cards)}
  </div>
  <footer>Streaming is temporary — this page and its files are deleted automatically when the link expires.</footer>
</div>

<dialog id="player">
  <div class="dlgbar"><span id="pname"></span><button id="close">Close</button></div>
  <video id="vid" controls playsinline preload="metadata"></video>
</dialog>

<script>
const EXPIRES = {expires};
const exp = document.getElementById('exp');
function tick() {{
  let s = EXPIRES - Math.floor(Date.now() / 1000);
  if (s <= 0) {{ exp.textContent = 'now'; exp.className = 'soon'; return; }}
  const d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60);
  exp.textContent = d > 0 ? `in ${{d}} day${{d > 1 ? 's' : ''}}` : (h > 0 ? `in ${{h}}h ${{m}}m` : `in ${{m}}m`);
  if (d < 1) exp.className = 'soon';
}}
tick(); setInterval(tick, 30000);

const dlg = document.getElementById('player'), vid = document.getElementById('vid'),
      pname = document.getElementById('pname');
document.querySelectorAll('.poster').forEach(function (p) {{
  p.addEventListener('click', function () {{
    vid.src = p.dataset.src;
    pname.textContent = p.dataset.name;
    dlg.showModal();
    vid.play().catch(function () {{}});
  }});
}});
function shut() {{ vid.pause(); vid.removeAttribute('src'); vid.load(); dlg.close(); }}
document.getElementById('close').addEventListener('click', shut);
dlg.addEventListener('close', function () {{ vid.pause(); }});
dlg.addEventListener('click', function (e) {{ if (e.target === dlg) shut(); }});
</script>
</body>
</html>''')
