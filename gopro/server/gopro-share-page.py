#!/usr/bin/env python3
"""Render a share collection's .meta.json as its index.html.

Wears the shared elyesghazel design: tokens, components, theme and fonts are served
same-origin under /_eg/ (the design site's public/ dir, mounted into the share
container), so a page never depends on another host being up.

Usage: gopro-share-page.py <dir>/.meta.json [host]  > <dir>/index.html
Streaming (v/) and forced downloads (dl/v/, dl/4k/) keep separate URLs.
"""
import html
import json
import os
import sys
from datetime import datetime, timezone
from string import Template
from urllib.parse import quote

EG = "/_eg"


def human(size):
    size = float(size or 0)
    if not size:
        return "-"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit in ("B", "KB") else f"{size:.1f} {unit}"
        size /= 1024


def label(height):
    height = int(height or 0)
    if height >= 2100:
        return "4k"
    if height >= 1400:
        return "1440p"
    if height >= 1000:
        return "1080p"
    return f"{height}p" if height else "original"


def clock(seconds):
    seconds = int(round(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


def shot_date(value):
    """ffprobe creation_time (ISO) -> datetime, or None."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def day(dt):
    return f"{dt.day} {dt.strftime('%b').lower()} {dt.year}"


def span(dates):
    if not dates:
        return ""
    first, last = min(dates), max(dates)
    if first.date() == last.date():
        return day(first)
    if (first.year, first.month) == (last.year, last.month):
        return f"{first.day}-{day(last)}"
    return f"{day(first)} - {day(last)}"


def esc(value):
    return html.escape(str(value), quote=True)


PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>'


def render(meta, token="", host="share.elyesghazel.ch"):
    items = meta.get("items") or []
    expires = int(meta["expires"])
    expiry = datetime.fromtimestamp(expires, timezone.utc)
    title = str(meta.get("title") or "GoPro")
    dates = [d for d in (shot_date(i.get("shot")) for i in items) if d]
    when = span(dates)

    cards, clips = [], []
    for position, item in enumerate(items, 1):
        filename = str(item["file"])
        enc = quote(filename, safe="")
        name = filename.rsplit(".", 1)[0].replace("_", " ")
        thumb = quote(str(item.get("thumb") or ""), safe="")
        stream_q = label(item.get("h"))
        downloads = [{"href": f"dl/v/{enc}", "label": stream_q, "note": human(item.get("size"))}]
        if item.get("orig"):
            downloads.append({"href": f"dl/4k/{quote(str(item['orig']), safe='')}",
                              "label": f"{label(item.get('origH') or 2160)} original",
                              "note": human(item.get("origSize"))})
        shot = shot_date(item.get("shot"))
        clips.append({"src": f"v/{enc}", "name": name, "poster": f"t/{thumb}" if thumb else "",
                      "downloads": downloads})

        poster = (f'<img src="t/{thumb}" alt="" loading="lazy" decoding="async">' if thumb else
                  '<span class="no-poster">no preview frame</span>')
        buttons = "".join(
            f'<a class="btn btn-sm{" is-orig" if i else ""}" href="{d["href"]}" download '
            f'aria-label="download {esc(name)}, {esc(d["label"])}">'
            f'{esc(d["label"])} <span class="faint">{esc(d["note"])}</span> <span class="arr">&darr;</span></a>'
            for i, d in enumerate(downloads))
        meta_bits = [f"{position:02d}"]
        if item.get("w"):
            meta_bits.append(f'{int(item["w"])}x{int(item["h"])}')
        if shot:
            meta_bits.append(f'{day(shot)}, {shot.strftime("%H:%M")}')
        cards.append(f'''<article class="clip card" id="clip-{position}">
<button class="poster" type="button" data-i="{position - 1}" aria-label="play {esc(name)}">{poster}<span class="play">{PLAY}</span><span class="dur num">{clock(item.get("dur"))}</span></button>
<div class="clip-body"><p class="clip-meta num">{" <span>/</span> ".join(esc(b) for b in meta_bits)}</p>
<h3 title="{esc(filename)}">{esc(name)}</h3>
<div class="clip-dl">{buttons}</div></div></article>''')

    count = len(items)
    total_size = sum(int(i.get("size") or 0) for i in items)
    orig_size = sum(int(i.get("origSize") or 0) for i in items)
    runtime = clock(sum(i.get("dur") or 0 for i in items))
    clip_word = "clip" if count == 1 else "clips"
    summary = f"{count} {clip_word}, {runtime}" + (f", {when}" if when else "")
    first_thumb = next((c["poster"] for c in clips if c["poster"]), "")
    base = f"https://{host}/{token}/" if token else ""
    og_image = (f'<meta property="og:image" content="{esc(base + first_thumb)}">\n'
                '<meta name="twitter:card" content="summary_large_image">'
                if base and first_thumb else '<meta name="twitter:card" content="summary">')
    size_cell = human(total_size)
    if orig_size:
        size_cell += f' <small>+ {human(orig_size)} 4k</small>'
    dl_all = ('<button class="btn btn-sm" type="button" id="dl-all">download all '
              '<span class="arr">&darr;</span></button>' if count > 1 else "")
    empty = ('<div class="empty"><p class="faint">// --</p><p class="ink">no clips in this collection</p>'
             '<p class="hint">ask elyes for an updated link.</p></div>')

    return PAGE.substitute(
        eg=EG, title=esc(title), summary=esc(summary), og_image=og_image,
        og_url=f'<meta property="og:url" content="{esc(base)}">' if base else "",
        when=f'<span class="aside">{esc(when)}</span>' if when else "",
        count=count, clip_word=clip_word, runtime=runtime, size=size_cell,
        expires=expires, expiry_iso=expiry.isoformat(), expiry_date=day(expiry),
        dl_all=dl_all, cards="\n".join(cards) if cards else empty,
        clips=json.dumps(clips, ensure_ascii=False).replace("</", "<\\/"),
    )


PAGE = Template(r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="dark light">
<title>$title - shared clips</title>
<meta name="description" content="$summary. Shared by Elyes.">
<meta property="og:type" content="website">
<meta property="og:site_name" content="share.elyesghazel.ch">
<meta property="og:title" content="$title">
<meta property="og:description" content="$summary. Watch or download until $expiry_date.">
$og_url
$og_image
<link rel="icon" href="$eg/logo/web/favicon.ico" sizes="32x32">
<link rel="icon" href="$eg/logo/web/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="$eg/logo/web/apple-touch-icon.png">
<script src="$eg/theme.js"></script>
<link rel="stylesheet" href="$eg/tokens.css">
<link rel="stylesheet" href="$eg/components.css">
<style>
.wrap{max-width:var(--measure-wide)}
.header .theme-toggle{margin-left:auto}
.hero{padding:var(--sp-16) 0 var(--sp-10)}
.hero h1{color:var(--ink);font-size:clamp(28px,5vw,var(--fs-2xl));font-weight:var(--fw-regular);line-height:var(--lh-tight);letter-spacing:var(--tracking-tight);overflow-wrap:anywhere}
.hero .lede{margin-top:var(--sp-4);max-width:36rem;color:var(--dim);font-size:var(--fs-md)}
.stats{margin-bottom:var(--sp-12)}
.stat-value small{font-size:var(--fs-xs)}
#exp-cell.soon .stat-value,#exp-cell.soon .stat-label{color:var(--warn)}
.bar{display:flex;align-items:center;justify-content:space-between;gap:var(--sp-4);margin-bottom:var(--sp-6)}
.bar .section-label{flex:1;margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,20rem),1fr));gap:var(--sp-6)}
.clip{display:flex;flex-direction:column;overflow:hidden;min-width:0;transition:border-color var(--dur-1) ease}
.clip:hover,.clip.is-current{border-color:var(--rule-strong)}
.clip.is-current .clip-meta{color:var(--accent)}
.poster{position:relative;display:block;width:100%;aspect-ratio:16/9;padding:0;border:0;border-bottom:1px solid var(--rule);background:#0a0a0a;color:#fff;overflow:hidden;cursor:pointer}
.poster img{display:block;width:100%;height:100%;object-fit:cover;transition:transform 700ms var(--ease)}
.poster:hover img{transform:scale(1.025)}
.play{position:absolute;inset:0;margin:auto;display:grid;place-items:center;width:48px;height:48px;border:1px solid rgba(255,255,255,.5);border-radius:50%;background:rgba(0,0,0,.55);transition:background-color var(--dur-1) ease}
.poster:hover .play{background:rgba(0,0,0,.85)}
.play svg{width:18px;height:18px;fill:currentColor;transform:translateX(1px)}
.dur{position:absolute;right:var(--sp-2);bottom:var(--sp-2);padding:1px 6px;border-radius:var(--radius-1);background:rgba(0,0,0,.7);font-size:var(--fs-xs)}
.no-poster{display:grid;place-items:center;height:100%;color:#8a8a8a;font-size:var(--fs-xs)}
.clip-body{display:flex;flex-direction:column;flex:1;gap:var(--sp-2);padding:var(--sp-4) var(--sp-5) var(--sp-5)}
.clip-meta{color:var(--faint);font-size:var(--fs-xs)}
.clip-meta span{color:var(--rule-strong)}
.clip h3{color:var(--ink);font-size:var(--fs-md);font-weight:var(--fw-regular);line-height:var(--lh-snug);overflow-wrap:anywhere}
.clip-dl{display:flex;flex-wrap:wrap;gap:var(--sp-2);margin-top:auto;padding-top:var(--sp-3)}
.clip-dl .btn{flex:1 1 auto}
.btn .arr{transition:transform var(--dur-2) var(--ease)}
.btn:hover .arr{transform:translateY(2px)}
.empty{grid-column:1/-1;display:grid;gap:var(--sp-2);padding:var(--sp-12) var(--sp-6);border:1px dashed var(--rule-strong);border-radius:var(--radius-2);text-align:center}
.footer{display:flex;flex-wrap:wrap;justify-content:space-between;gap:var(--sp-4);margin-top:var(--sp-16);padding:var(--sp-6) 0 var(--sp-10);border-top:1px solid var(--rule);color:var(--faint);font-size:var(--fs-xs)}
dialog{width:min(1180px,calc(100% - 32px));max-width:none;max-height:calc(100dvh - 32px);padding:0;border:1px solid var(--rule-strong);border-radius:var(--radius-2);background:var(--bg-raised);color:var(--body);overflow:auto}
dialog::backdrop{background:rgba(0,0,0,.9)}
.pl-head,.pl-foot{display:flex;align-items:center;gap:var(--sp-3);padding:var(--sp-3) var(--sp-4)}
.pl-head{border-bottom:1px solid var(--rule)}
.pl-foot{border-top:1px solid var(--rule);flex-wrap:wrap}
.pl-head h2{flex:1;min-width:0;color:var(--ink);font-size:var(--fs-sm);font-weight:var(--fw-regular);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pl-pos{color:var(--faint);font-size:var(--fs-xs)}
dialog video{display:block;width:100%;max-height:calc(100dvh - 150px);background:#000}
.pl-err{padding:var(--sp-3) var(--sp-4);color:var(--warn);font-size:var(--fs-xs)}
.pl-nav{display:flex;gap:var(--sp-2);margin-left:auto}
.pl-keys{color:var(--faint);font-size:var(--fs-2xs)}
@media (max-width:640px){.wrap{padding:0 var(--sp-4)}.hero{padding:var(--sp-10) 0 var(--sp-8)}.pl-keys{display:none}dialog{width:100%;max-height:100dvh;border-radius:0;border-width:1px 0}dialog video{max-height:calc(100dvh - 170px)}}
</style>
</head>
<body>
<header class="header"><div class="wrap header-in">
<a class="wordmark" href="https://elyesghazel.ch" rel="noreferrer"><span class="sub">share.</span>elyesghazel<span class="tld">.ch</span></a>
<button class="theme-toggle" type="button" data-theme-toggle aria-label="toggle theme"><svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M8 1a7 7 0 0 1 0 14z" fill="currentColor"/></svg></button>
</div></header>
<main class="wrap">
<section class="hero">
<h2 class="section-label"><span class="slashes">//</span> shared clips $when</h2>
<h1>$title</h1>
<p class="lede">Clips Elyes sent you. Play them here, download the ones you want to keep.</p>
</section>
<div class="stats">
<div class="stat"><span class="stat-value num">$count</span><span class="stat-label">$clip_word</span></div>
<div class="stat"><span class="stat-value num">$runtime</span><span class="stat-label">runtime</span></div>
<div class="stat"><span class="stat-value num">$size</span><span class="stat-label">to download</span></div>
<div class="stat" id="exp-cell"><span class="stat-value num" id="exp-left">$expiry_date</span><span class="stat-label"><time id="exp" data-expires="$expires" datetime="$expiry_iso">until $expiry_date</time></span></div>
</div>
<section aria-labelledby="clips-h">
<div class="bar"><h2 class="section-label" id="clips-h"><span class="slashes">//</span> clips</h2>$dl_all</div>
<div class="grid">$cards</div>
</section>
<footer class="footer"><span>anyone with this link can watch and download. it deletes itself on $expiry_date.</span><a class="link" href="https://elyesghazel.ch" rel="noreferrer">elyesghazel.ch &rarr;</a></footer>
</main>
<dialog id="player" aria-labelledby="pl-name">
<div class="pl-head"><span class="pl-pos num" id="pl-pos"></span><h2 id="pl-name">clip</h2><button class="btn btn-sm btn-ghost" type="button" id="pl-close">close &times;</button></div>
<video id="video" controls playsinline preload="metadata"></video>
<p class="pl-err" id="pl-err" role="status" hidden>this browser can't play the preview. download the clip and watch it locally.</p>
<div class="pl-foot"><div class="clip-dl" id="pl-dl" style="margin:0;padding:0"></div><span class="pl-keys">&larr; &rarr; switch clips</span><div class="pl-nav"><button class="btn btn-sm" type="button" id="pl-prev">&larr; prev</button><button class="btn btn-sm" type="button" id="pl-next">next &rarr;</button></div></div>
</dialog>
<script>
(function () {
  var clips = $clips;
  var $$ = function (id) { return document.getElementById(id); };

  // expiry countdown, local time
  var exp = Number($$('exp').dataset.expires) * 1000;
  var fmt = new Intl.DateTimeFormat(undefined, {day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'});
  $$('exp').textContent = 'until ' + fmt.format(new Date(exp));
  function tick() {
    var s = Math.floor((exp - Date.now()) / 1000), d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60);
    $$('exp-cell').classList.toggle('soon', s < 86400);
    $$('exp-left').textContent = s <= 0 ? 'expired' : d > 0 ? d + (d === 1 ? ' day' : ' days') : h > 0 ? h + 'h ' + m + 'm' : Math.max(m, 1) + 'm';
  }
  tick(); setInterval(tick, 30000);

  // download all: one anchor click per file, spaced out so browsers don't drop them
  var all = $$('dl-all');
  if (all) all.addEventListener('click', function () {
    clips.forEach(function (c, i) {
      setTimeout(function () { var a = document.createElement('a'); a.href = c.downloads[c.downloads.length - 1].href; a.download = ''; document.body.appendChild(a); a.click(); a.remove(); }, i * 800);
    });
  });

  // player
  var player = $$('player'), video = $$('video'), err = $$('pl-err'), cur = -1;
  function show(i) {
    if (i < 0 || i >= clips.length) return;
    cur = i; var c = clips[i];
    err.hidden = true;
    video.poster = c.poster; video.src = c.src;
    $$('pl-name').textContent = c.name;
    $$('pl-pos').textContent = String(i + 1).padStart(2, '0') + ' / ' + String(clips.length).padStart(2, '0');
    $$('pl-dl').innerHTML = '';
    c.downloads.forEach(function (d) {
      var a = document.createElement('a'); a.className = 'btn btn-sm'; a.href = d.href; a.download = '';
      a.innerHTML = '<span></span> <span class="faint"></span> <span class="arr">&darr;</span>';
      a.children[0].textContent = d.label; a.children[1].textContent = d.note;
      $$('pl-dl').appendChild(a);
    });
    $$('pl-prev').disabled = i === 0; $$('pl-next').disabled = i === clips.length - 1;
    document.querySelectorAll('.clip').forEach(function (el, j) { el.classList.toggle('is-current', j === i); });
    history.replaceState(null, '', '#clip-' + (i + 1));
    if (!player.open) player.showModal();
    video.play().catch(function () {});
  }
  document.querySelectorAll('.poster').forEach(function (b) { b.addEventListener('click', function () { show(Number(b.dataset.i)); }); });
  $$('pl-prev').addEventListener('click', function () { show(cur - 1); });
  $$('pl-next').addEventListener('click', function () { show(cur + 1); });
  $$('pl-close').addEventListener('click', function () { player.close(); });
  player.addEventListener('click', function (e) { if (e.target === player) player.close(); });
  player.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight' && e.shiftKey === false && document.activeElement !== video) { e.preventDefault(); show(cur + 1); }
    if (e.key === 'ArrowLeft' && e.shiftKey === false && document.activeElement !== video) { e.preventDefault(); show(cur - 1); }
  });
  video.addEventListener('ended', function () { if (cur < clips.length - 1) show(cur + 1); });
  video.addEventListener('error', function () { if (video.getAttribute('src')) err.hidden = false; });
  player.addEventListener('close', function () {
    video.pause(); video.removeAttribute('src'); video.load();
    var el = document.getElementById('clip-' + (cur + 1));
    history.replaceState(null, '', location.pathname);
    if (el) el.querySelector('.poster').focus({preventScroll: true});
  });

  // #clip-3 opens that clip (handy for pointing someone at one moment)
  var m = /^#clip-(\d+)$$/.exec(location.hash);
  if (m && clips[m[1] - 1]) { document.getElementById('clip-' + m[1]).scrollIntoView(); show(m[1] - 1); }
})();
</script>
</body>
</html>
''')


if __name__ == "__main__":
    path = sys.argv[1]
    token = os.path.basename(os.path.dirname(os.path.abspath(path)))
    host = sys.argv[2] if len(sys.argv) > 2 else "share.elyesghazel.ch"
    with open(path) as source:
        print(render(json.load(source), token, host))
