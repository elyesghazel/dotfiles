#!/usr/bin/env python3
"""Render a self-contained GoPro gallery; streaming and downloads keep separate URLs."""
import html
import json
import sys
from datetime import datetime, timezone
from string import Template
from urllib.parse import quote


def human(size):
    if not size:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit in ("B", "KB") else f"{size:.1f} {unit}"
        size /= 1024


def label(height):
    height = int(height or 0)
    if height >= 2100:
        return "4K"
    if height >= 1400:
        return "1440p"
    if height >= 1000:
        return "1080p"
    return f"{height}p" if height else "Original"


def clock(seconds):
    seconds = int(seconds or 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


DOWNLOAD_ICON = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2v10m-4-4 4 4 4-4M3 13v4h14v-4"/></svg>'
PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 11 7-11 7z"/></svg>'


def render(meta):
    items = meta["items"]
    expires = int(meta["expires"])
    expiry = datetime.fromtimestamp(expires, timezone.utc)
    cards = []
    for position, item in enumerate(items, 1):
        filename = str(item["file"])
        encoded = quote(filename, safe="")
        name = html.escape(filename.rsplit(".", 1)[0].replace("_", " "), quote=True)
        thumb = quote(str(item.get("thumb") or ""), safe="")
        poster = (f'<img src="t/{thumb}" alt="" loading="lazy" decoding="async">' if thumb else
                  '<span class="no-poster">Preview unavailable<span>You can still play this clip</span></span>')
        resolution = f'{int(item["w"])} × {int(item["h"])}' if item.get("w") else "Video"
        stream_quality = label(item.get("h"))
        downloads = [f'<a class="download" href="dl/v/{encoded}" aria-label="Download {name}, {stream_quality} stream copy">'
                     f'{DOWNLOAD_ICON}<span><b>{stream_quality}</b><small>Stream copy · {human(item["size"])}</small></span></a>']
        if item.get("orig"):
            original = quote(str(item["orig"]), safe="")
            quality = label(item.get("origH") or 2160)
            downloads.append(f'<a class="download original" href="dl/4k/{original}" aria-label="Download {name}, {quality} original">'
                             f'{DOWNLOAD_ICON}<span><b>{quality} original</b><small>Full-quality file · {human(item["origSize"])}</small></span></a>')
        cards.append(f'''<article class="clip">
<button class="poster" type="button" data-src="v/{encoded}" data-name="{name}" aria-label="Play {name}">
{poster}<span class="play">{PLAY_ICON}</span><span class="duration">{clock(item.get("dur"))}</span>
</button>
<div class="clip-body"><p class="clip-index">{position:02d} <span>/ {resolution}</span></p>
<h3 title="{html.escape(filename, quote=True)}">{name}</h3>
<div class="download-section"><p class="section-label">Save this clip</p><div class="downloads">{"".join(downloads)}</div></div>
</div></article>''')
    empty = '<div class="empty"><h3>No clips in this collection</h3><p>Ask the sender for an updated link.</p></div>'
    return PAGE.substitute(
        title=html.escape(str(meta["title"]), quote=True),
        count=len(items), clip_word="clip" if len(items) == 1 else "clips",
        runtime=clock(sum(item.get("dur") or 0 for item in items)),
        size=human(sum(item["size"] for item in items)),
        expires=expires, expiry_iso=expiry.isoformat(),
        expiry_full=expiry.strftime("%d %B %Y, %H:%M UTC"), expiry_date=expiry.strftime("%d %b %Y"),
        cards="\n".join(cards) if cards else empty,
    )


PAGE = Template(r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="dark light">
<title>$title · Shared clips</title>
<script>
try { const theme = localStorage.getItem('theme'); if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme; } catch {}
</script>
<style>
:root{color-scheme:dark;--bg:#000;--panel:#0b0b0b;--hover:#141414;--ink:#fff;--dim:#a6a6a6;--faint:#8a8a8a;--rule:#232323;--strong:#3a3a3a;--info:#74a7e6;--info-soft:rgba(116,167,230,.12);--warn:#d9ad5b;--warn-soft:rgba(217,173,91,.12);--font:ui-monospace,"SFMono-Regular",Menlo,Consolas,"DejaVu Sans Mono",monospace}
@media(prefers-color-scheme:light){:root:not([data-theme="dark"]){color-scheme:light;--bg:#fafafa;--panel:#fff;--hover:#f0f0f0;--ink:#0a0a0a;--dim:#555;--faint:#6b6b6b;--rule:#e3e3e3;--strong:#c4c4c4;--info:#1f5fb4;--info-soft:rgba(31,95,180,.09);--warn:#8f5f00;--warn-soft:rgba(143,95,0,.1)}}
:root[data-theme="light"]{color-scheme:light;--bg:#fafafa;--panel:#fff;--hover:#f0f0f0;--ink:#0a0a0a;--dim:#555;--faint:#6b6b6b;--rule:#e3e3e3;--strong:#c4c4c4;--info:#1f5fb4;--info-soft:rgba(31,95,180,.09);--warn:#8f5f00;--warn-soft:rgba(143,95,0,.1)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 var(--font);-webkit-font-smoothing:antialiased}button,a{-webkit-tap-highlight-color:transparent}button{font:inherit}a{color:inherit}button:focus-visible,a:focus-visible{outline:2px solid var(--info);outline-offset:4px}svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}button{cursor:pointer}.wrap{max-width:1400px;margin:0 auto;padding:0 32px}
.bar{border-bottom:1px solid var(--rule)}.bar .wrap{display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:72px}.brand{text-decoration:none;letter-spacing:-.04em;font-size:15px}.brand span{color:var(--faint)}.bar-actions{display:flex;align-items:center;gap:14px}.bar-caption{font-size:12px;color:var(--faint)}.icon-button{display:inline-grid;place-items:center;width:38px;height:38px;border:1px solid var(--rule);border-radius:2px;background:none;color:var(--ink)}.icon-button:hover{background:var(--hover);border-color:var(--strong)}
.hero{padding:64px 0 36px}.eyebrow,.section-label{text-transform:uppercase;letter-spacing:.12em;font-size:11px;color:var(--faint);margin:0}.eyebrow{display:flex;align-items:center;gap:12px;margin-bottom:24px}.eyebrow::before{content:"//";color:var(--info)}.hero-row{display:flex;align-items:flex-start;justify-content:space-between;gap:32px}.hero-copy{min-width:0;max-width:850px}h1{font-size:clamp(30px,4.6vw,54px);line-height:1.15;letter-spacing:-.055em;font-weight:400;margin:0 0 20px;overflow-wrap:anywhere}.intro{font-size:15px;color:var(--dim);margin:0;max-width:640px}.badge{display:inline-flex;align-items:center;gap:8px;white-space:nowrap;font-size:12px;padding:6px 10px;border-radius:2px;background:var(--warn-soft);color:var(--warn)}.badge::before{content:"";width:6px;height:6px;background:currentColor;border-radius:50%;flex:none}.share-access{flex:none;padding-top:4px}.access-note{color:var(--faint);font-size:11px;margin:9px 0 0;text-align:right}
.collection-info{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:26px 0 28px;border-bottom:1px solid var(--rule)}.stats{display:flex;gap:40px;margin:0}.stat{display:flex;flex-direction:column-reverse;gap:3px}.stat dt{font-size:11px;color:var(--faint)}.stat dd{margin:0;font-size:18px;letter-spacing:-.04em;font-variant-numeric:tabular-nums}.expiry{font-size:12px;text-align:right;color:var(--dim)}.expiry time{color:var(--ink);font-weight:500}.expiry p{margin:2px 0 0;color:var(--faint);font-size:11px}.expiry.soon{color:var(--warn)}.expiry.soon time,.expiry.soon p{color:var(--warn)}
.collection-heading{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:32px 0 20px}.collection-heading h2{font-weight:400;font-size:13px;margin:0}.collection-heading h2::before{content:"// ";color:var(--faint)}.collection-heading span{color:var(--faint);font-size:11px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:24px;align-items:stretch}.clip{border:1px solid var(--rule);border-radius:4px;overflow:hidden;background:var(--panel);display:flex;flex-direction:column;min-width:0}.poster{display:block;position:relative;isolation:isolate;padding:0;width:100%;border:0;color:#fff;background:#101010;aspect-ratio:16/9;overflow:hidden;text-align:left}.poster::after{content:"";position:absolute;inset:45% 0 0;background:linear-gradient(transparent,rgba(0,0,0,.55));z-index:0;pointer-events:none}.poster img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .3s ease}.poster:hover img{transform:scale(1.025)}.play{position:absolute;inset:0;margin:auto;display:grid;place-items:center;width:54px;height:54px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.45);z-index:1;transition:background .15s}.play svg{width:22px;height:22px;fill:currentColor;stroke-width:0;transform:translateX(-1px)}.poster:hover .play{background:rgba(0,0,0,.8)}.duration{position:absolute;right:14px;bottom:12px;z-index:1;font-size:12px;color:#fff;font-variant-numeric:tabular-nums}.no-poster{display:grid;place-content:center;gap:4px;width:100%;height:100%;padding:24px 24px 100px;text-align:center;color:#b0b0b0;font-size:12px}.no-poster span{font-size:10px;color:#8a8a8a}
.clip-body{padding:22px;display:flex;flex-direction:column;flex:1}.clip-index{font-size:10px;color:var(--info);margin:0 0 9px;letter-spacing:.05em}.clip-index span{color:var(--faint)}h3{font-size:16px;line-height:1.5;font-weight:500;letter-spacing:-.025em;margin:0 0 24px;overflow-wrap:anywhere}.download-section{margin-top:auto;border-top:1px solid var(--rule);padding-top:16px}.download-section .section-label{font-size:10px;margin-bottom:10px}.downloads{display:flex;gap:10px;flex-wrap:wrap}.download{display:flex;align-items:center;gap:10px;flex:1 1 120px;min-height:58px;padding:9px 12px;border:1px solid var(--rule);border-radius:2px;text-decoration:none;transition:background .15s,border-color .15s}.download:hover{border-color:var(--strong);background:var(--hover)}.download svg{width:16px;height:16px;flex:none;color:var(--dim)}.download span{display:grid;gap:1px}.download b{font-size:12px;font-weight:500}.download small{font-size:10px;color:var(--faint)}.download.original{border-color:color-mix(in srgb,var(--info) 35%,var(--rule))}.download.original b,.download.original svg{color:var(--info)}.empty{grid-column:1/-1;border:1px dashed var(--rule);padding:48px 24px;text-align:center;color:var(--dim)}.empty h3{color:var(--ink);margin-bottom:8px}.empty p{margin:0}
footer{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;border-top:1px solid var(--rule);margin-top:48px;padding:24px 0 40px;color:var(--faint);font-size:11px}footer p{margin:0;max-width:680px}footer span{white-space:nowrap;color:var(--dim)}dialog{width:min(1120px,calc(100% - 32px));max-width:none;max-height:calc(100dvh - 32px);padding:0;border:1px solid var(--strong);border-radius:4px;background:var(--panel);color:var(--ink);overflow:auto}dialog::backdrop{background:rgba(0,0,0,.85)}.player-bar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:14px 18px;border-bottom:1px solid var(--rule)}.player-bar h2{margin:0;font-size:13px;font-weight:400;overflow-wrap:anywhere;min-width:0}.player-close{background:none;color:var(--ink);border:1px solid var(--rule);border-radius:2px;padding:7px 12px;flex:none;min-height:38px}.player-close:hover{background:var(--hover)}dialog video{display:block;width:100%;max-height:calc(100dvh - 140px);background:#000}.playback-error{padding:16px 20px;color:var(--warn);font-size:12px;margin:0}
@media(min-width:1100px){.clip:only-child{max-width:calc((100% - 24px)/2)}}
@media(max-width:700px){.wrap{padding:0 20px}.bar .wrap{min-height:62px}.bar-caption{display:none}.hero{padding-top:40px}.hero-row{flex-direction:column;gap:24px}.access-note{text-align:left}.collection-info{align-items:flex-start;gap:24px}.stats{gap:26px}.stat dd{font-size:16px}.expiry{text-align:left}.grid{gap:20px}.collection-heading span{display:none}footer{flex-direction:column;gap:12px}.clip-body{padding:20px}.hero .eyebrow{margin-bottom:18px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important;scroll-behavior:auto!important}}
</style>
</head>
<body>
<header class="bar"><div class="wrap"><span class="brand">elyesghazel<span> / shared clips</span></span><div class="bar-actions"><span class="bar-caption">Good moments, passed along.</span><button id="theme-toggle" class="icon-button" type="button" aria-label="Switch color theme"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7"/><path d="M10 3a7 7 0 0 1 0 14z" fill="currentColor" stroke="none"/></svg></button></div></div></header>
<main class="wrap">
<section class="hero" aria-labelledby="collection-title"><p class="eyebrow">A collection from Elyes</p><div class="hero-row"><div class="hero-copy"><h1 id="collection-title">$title</h1><p class="intro">Watch here. Download the moments you want to keep.</p></div><div class="share-access"><span class="badge">Anyone with the link</span><p class="access-note">No account needed. Forward thoughtfully.</p></div></div></section>
<section class="collection-info" aria-label="Collection details"><dl class="stats"><div class="stat"><dt>In this collection</dt><dd>$count $clip_word</dd></div><div class="stat"><dt>Total runtime</dt><dd>$runtime</dd></div><div class="stat"><dt>Stream copies</dt><dd>$size</dd></div></dl><div class="expiry" id="expiry"><span id="expiry-label">Link expires</span> <time id="exp" data-expires="$expires" datetime="$expiry_iso" title="$expiry_full">$expiry_date</time><p id="expiry-relative">Save your favourites before then.</p></div></section>
<section aria-labelledby="clips-heading"><div class="collection-heading"><h2 id="clips-heading">The collection</h2><span>Play a preview · choose a download below</span></div><div class="grid">$cards</div></section>
<footer><p>These clips are shared through a temporary link, not a private account. Anyone with the link can watch and download. Save a copy before the link expires.</p><span>Shared by Elyes Ghazel</span></footer>
</main>
<dialog id="player" aria-labelledby="player-name"><div class="player-bar"><h2 id="player-name">Video preview</h2><button id="close" class="player-close" type="button">Close <span aria-hidden="true">×</span></button></div><video id="video" controls playsinline preload="metadata"></video><p id="playback-error" class="playback-error" role="status" hidden>This browser couldn’t play the preview. Close the player and use a download button to watch it locally.</p></dialog>
<script>
const themeToggle = document.getElementById('theme-toggle');
function currentTheme() { return document.documentElement.dataset.theme || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'); }
function updateThemeLabel() { themeToggle.setAttribute('aria-label', 'Switch to ' + (currentTheme() === 'dark' ? 'light' : 'dark') + ' theme'); }
updateThemeLabel();
themeToggle.addEventListener('click', function () {
  const theme = currentTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('theme', theme); } catch {}
  updateThemeLabel();
});
const expiresAt = Number(document.getElementById('exp').dataset.expires);
const expiry = document.getElementById('expiry');
const expiryTime = document.getElementById('exp');
const expiryRelative = document.getElementById('expiry-relative');
expiryTime.textContent = new Intl.DateTimeFormat(undefined, {day:'numeric',month:'short',year:'numeric'}).format(new Date(expiresAt * 1000));
expiryTime.title = new Intl.DateTimeFormat(undefined, {dateStyle:'full',timeStyle:'short'}).format(new Date(expiresAt * 1000));
function updateExpiry() {
  const remaining = expiresAt - Math.floor(Date.now() / 1000);
  expiry.classList.toggle('soon', remaining < 86400);
  if (remaining <= 0) {
    document.getElementById('expiry-label').textContent = 'Link expired';
    expiryRelative.textContent = 'Ask Elyes for a fresh link if the files are unavailable.';
    return;
  }
  const days = Math.floor(remaining / 86400);
  const hours = Math.floor(remaining % 86400 / 3600);
  const minutes = Math.floor(remaining % 3600 / 60);
  const relative = days > 0 ? days + (days === 1 ? ' day' : ' days') : hours > 0 ? hours + 'h ' + minutes + 'm' : minutes > 0 ? minutes + 'm' : 'less than a minute';
  expiryRelative.textContent = 'Expires in ' + relative + ' · download to keep a copy.';
}
updateExpiry();
setInterval(updateExpiry, 30000);
const player = document.getElementById('player');
const video = document.getElementById('video');
const playbackError = document.getElementById('playback-error');
document.querySelectorAll('.poster').forEach(function (poster) {
  poster.addEventListener('click', function () {
    playbackError.hidden = true;
    video.src = poster.dataset.src;
    document.getElementById('player-name').textContent = poster.dataset.name;
    player.showModal();
    video.play().catch(function () {});
  });
});
function closePlayer() { player.close(); }
document.getElementById('close').addEventListener('click', closePlayer);
player.addEventListener('click', function (event) { if (event.target === player) closePlayer(); });
player.addEventListener('close', function () { video.pause(); video.removeAttribute('src'); video.load(); playbackError.hidden = true; });
video.addEventListener('error', function () { if (video.hasAttribute('src')) playbackError.hidden = false; });
</script>
</body>
</html>
''')


if __name__ == "__main__":
    with open(sys.argv[1]) as source:
        print(render(json.load(source)))
