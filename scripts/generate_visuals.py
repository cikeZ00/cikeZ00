#!/usr/bin/env python3
"""Renders the animated YoRHa-style profile visuals: terminal feed, section
separators, live commit telemetry and shutdown footer.

Commit numbers come from the GitHub API, so the panels show real data.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BG = "#0b0b0b"
PAPER = "#d8d3c4"
MUTED = "#827f76"
GOLD = "#c9bea4"
DIM = "#3a3730"
INK = "#171717"

LOGIN = os.environ.get("GITHUB_LOGIN") or "cikeZ00"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

# Android units are shipped as Steam store art; all of it is fetched at build
# time and embedded, so the published SVGs never depend on a third-party hotlink.
IMAGES = {
    "hero": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/524220/library_hero.jpg",
    "unit": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/524220/"
    "ss_8b29f7e1ce9a8b9313dc3eb50dbe76a4cf94eef9.600x338.jpg",
}

# count.getloli.com rejects non-browser agents, so every asset fetch looks like
# one; Steam does not mind either way.
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def esc(value) -> str:
    return html.escape(str(value), quote=True)


# ---------------------------------------------------------------- GitHub data


def api(path: str, tries: int = 4):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"{LOGIN}-profile"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (403, 429) or attempt == tries - 1:
                raise SystemExit(f"GitHub API {error.code} for {path}")
            reset = int(error.headers.get("X-RateLimit-Reset") or 0) - int(time.time())
            time.sleep(max(5, min(reset + 2, 65)))
    raise SystemExit(f"GitHub API gave up on {path}")


def fetch_stats(login: str) -> dict:
    user = api(f"/users/{login}")
    repos, page = [], 1
    while True:
        chunk = api(f"/users/{login}/repos?per_page=100&page={page}&type=owner")
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1

    owned = [repo for repo in repos if not repo["fork"]]
    # shortcut: search caps total_count at 1000, split by year once it is hit
    total = api(f"/search/commits?q=author:{login}&per_page=1")["total_count"]

    this_year = datetime.now(timezone.utc).year
    years = {}
    for year in range(int(user["created_at"][:4]), this_year + 1):
        query = f"author:{login}+author-date:{year}-01-01..{year}-12-31"
        years[year] = api(f"/search/commits?q={query}&per_page=1")["total_count"]

    return {
        "login": user["login"],
        "commits": total,
        "year": this_year,
        "year_commits": years[this_year],
        "years": years,
        "stars": sum(repo["stargazers_count"] for repo in owned),
        "repos": user["public_repos"],
        "followers": user["followers"],
    }


def download(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return base64.b64encode(response.read()).decode("ascii")


# ------------------------------------------------------------------ SVG shell

# The panels carry no background of their own: the palette is a pair of CSS
# custom-property sets, so the same file reads as a light or dark terminal
# depending on the viewer's colour scheme.
THEME = """<style>
:root{--bg:transparent;--paper:#2c2b26;--muted:#6c675c;--gold:#8a7c5e;--dim:#cfc9ba;
--ink:rgba(20,20,18,.06);--grid:rgba(30,28,24,.12)}
.g-top{stop-color:#cbbd9f}.g-bot{stop-color:#877b63}
.b-top{stop-color:#b6a98b}.b-bot{stop-color:#6b6353}
@media (prefers-color-scheme:dark){:root{--paper:#d8d3c4;--muted:#827f76;--gold:#c9bea4;
--dim:#3a3730;--ink:#171717;--grid:rgba(185,176,156,.08)}
.g-top{stop-color:#f0e9d8}.g-bot{stop-color:#9c9077}
.b-top{stop-color:#c9bea4}.b-bot{stop-color:#6d6758}}
text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
</style>"""

# text sitting on artwork keeps its own light ink; the page palette would vanish
PHOTO_INK = "#e6e0cf"

VARS = {
    PAPER: "paper",
    MUTED: "muted",
    GOLD: "gold",
    DIM: "dim",
    INK: "ink",
    BG: "bg",
    "#b9b09c": "grid",
}


def themed(body: str) -> str:
    """Swap palette literals for CSS variables; one style attribute per tag."""
    for hex_value, name in VARS.items():
        for prop in ("fill", "stroke", "stop-color"):
            body = body.replace(f'{prop}="{hex_value}"', f'style="{prop}:var(--{name})"')
    for tag in re.findall(r"<[^>]+>", body):
        if tag.count('style="') > 1:
            raise SystemExit(f"conflicting theme attributes: {tag[:120]}")
    return body


def svg(body: str, width: int, height: int, title: str, extra: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
        f"{THEME}<defs>"
        f'<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">'
        f'<stop class="g-top"/><stop offset="1" class="g-bot"/></linearGradient>'
        f'<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">'
        f'<stop class="b-top"/><stop offset="1" class="b-bot"/></linearGradient>'
        f'<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
        f'<feGaussianBlur stdDeviation="2.6" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<path d="M24 0H0V24" fill="none" stroke="#b9b09c" stroke-opacity=".07"/></pattern>'
        f'<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1" fill="#000" fill-opacity=".22"/></pattern>'
        f"{extra}</defs>{themed(body)}</svg>"
    )


def ticks(x, y, w, h, arm=12, opacity=0.75) -> str:
    path = (
        f"M{x} {y + arm}V{y}H{x + arm}M{x + w - arm} {y}H{x + w}V{y + arm}"
        f"M{x + w} {y + h - arm}V{y + h}H{x + w - arm}M{x + arm} {y + h}H{x}V{y + h - arm}"
    )
    return f'<path d="{path}" fill="none" stroke="{GOLD}" stroke-opacity="{opacity}"/>'


def mark(cx, cy, size, colour=GOLD, dur=1.6, begin=0.0) -> str:
    """Status lamp: a YorHa diamond rather than a round bullet."""
    # negative begin only shifts the phase; skip it at zero, "-0.0s" is not a time
    phase = f'begin="-{begin}s" ' if begin else ""
    path = f"M{cx} {cy - size}L{cx + size} {cy}L{cx} {cy + size}L{cx - size} {cy}Z"
    return (
        f'<path d="{path}" fill="{colour}">'
        f'<animate attributeName="opacity" values="1;.18;1" dur="{dur}s" '
        f'{phase}repeatCount="indefinite"/></path>'
    )


def emblem(cx, cy, r=7) -> str:
    """Title-bar sigil: nested diamonds with HUD ticks."""
    return (
        f'<g transform="translate({cx} {cy})">'
        f'<path d="M-{r + 5} 0h3M{r + 2} 0h3" stroke="{GOLD}" stroke-opacity=".45"/>'
        f'<path d="M0 -{r}L{r} 0L0 {r}L-{r} 0Z" fill="none" stroke="{GOLD}" stroke-opacity=".65"/>'
        f'<path d="M0 -{r * .42}L{r * .42} 0L0 {r * .42}L-{r * .42} 0Z" fill="{GOLD}">'
        '<animate attributeName="opacity" values="1;.35;1" dur="3.4s" repeatCount="indefinite"/>'
        "</path></g>"
    )


CLIPS = iter(range(1000))


def marquee(text, x, y, width, dur, size=10, colour=MUTED, spacing=2) -> str:
    """Two copies exactly one window apart, so the wrap has no seam."""
    clip = f"m{next(CLIPS)}"
    body = (
        f'<clipPath id="{clip}"><rect x="{x}" y="{y - size - 5}" width="{width}" '
        f'height="{size + 12}"/></clipPath>'
        f'<g clip-path="url(#{clip})"><g>'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" '
        f'to="-{width} 0" dur="{dur}s" repeatCount="indefinite"/>'
    )
    for offset in (0, width):
        body += (
            f'<text x="{x + offset}" y="{y}" font-size="{size}" fill="{colour}" '
            f'letter-spacing="{spacing}" textLength="{width}" lengthAdjust="spacingAndGlyphs">'
            f"{esc(text)}</text>"
        )
    return body + "</g></g>"


# ------------------------------------------------------------------- terminal


def terminal_header(hero: str, stats: dict, width: int = 1200) -> str:
    bar, feed_h = 34, 388
    height = bar + feed_h + 40
    body = [
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
        f'<rect width="{width}" height="{height}" fill="url(#grid)"/>',
        # window chrome
        f'<rect width="{width}" height="{bar}" fill="{INK}"/>',
        f'<path d="M0 {bar}H{width}" stroke="{GOLD}" stroke-opacity=".45"/>',
        emblem(26, 17, 7),
        f'<text x="52" y="21" font-size="11" fill="{MUTED}" letter-spacing="1.5">'
        f'{esc(LOGIN)}@yorha:~$ feed --channel visual --unit 2B</text>',
        f'<text x="{width - 20}" y="21" text-anchor="end" font-size="10" fill="{GOLD}" '
        f'letter-spacing="2">CH.01 // RUINED CITY</text>',
        # image bay
        '<clipPath id="bay"><rect x="0" y="34" width="1200" height="388"/></clipPath>',
        '<g clip-path="url(#bay)">',
        '<g transform="translate(600 228)"><g>'
        '<animateTransform attributeName="transform" type="scale" values="1;1.05;1" dur="40s" '
        'calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1" '
        'repeatCount="indefinite"/>'
        '<g transform="translate(-600 -228)">'
        f'<image xlink:href="data:image/jpeg;base64,{hero}" x="0" y="34" width="1200" height="388" '
        'preserveAspectRatio="xMidYMid slice" filter="url(#warm)"/>'
        "</g></g></g>",
        f'<rect x="0" y="34" width="1200" height="388" fill="url(#scan)"/>',
        f'<rect x="0" y="30" width="1200" height="120" fill="url(#fadeTop)"/>',
        f'<rect x="0" y="292" width="1200" height="130" fill="url(#fadeBottom)"/>',
        f'<rect x="0" y="34" width="150" height="388" fill="url(#fadeLeft)"/>',
        f'<rect x="1050" y="34" width="150" height="388" fill="url(#fadeRight)"/>',
        # one-way sweep: it leaves the bay before it restarts, so no reverse pass
        f'<rect x="0" y="-40" width="1200" height="74" fill="url(#beam)" opacity=".9">'
        '<animate attributeName="y" values="-40;422" dur="9s" repeatCount="indefinite"/></rect>',
        # HUD marks over the feed
        f'<g stroke="{PHOTO_INK}" stroke-opacity=".5" fill="none">'
        f'<path d="M24 66V52H38M1176 66V52H1162M24 390V404H38M1176 390V404H1162"/></g>',
        f'<g font-size="9" fill="{PHOTO_INK}" fill-opacity=".75" letter-spacing="2">'
        f'<text x="24" y="52">FEED 01</text>'
        f'<text x="1176" y="52" text-anchor="end">FRAME 1920x620</text></g>',
        mark(1150, 300, 4, "#e8d8b0", 1.1, 0),
        f'<text x="1138" y="303" text-anchor="end" font-size="9" fill="{PHOTO_INK}" '
        f'letter-spacing="2">REC</text>',
        "</g>",
        ticks(0, 34, 1200, feed_h, 14, 0.5),
        # status bar
        f'<rect x="0" y="{bar + feed_h}" width="{width}" height="40" fill="{INK}"/>',
        f'<path d="M0 {bar + feed_h}H{width}" stroke="{GOLD}" stroke-opacity=".45"/>',
        mark(26, bar + feed_h + 20, 5, "#c96a5a", 1.4, 0),
        f'<text x="42" y="{bar + feed_h + 24}" font-size="10" fill="#c96a5a" letter-spacing="2">REC</text>',
        f'<text x="86" y="{bar + feed_h + 24}" font-size="10" fill="{GOLD}" letter-spacing="2">'
        "UNIT 2B // SIGNAL NOMINAL</text>",
        marquee(
            "NO DATA CORRUPTION  //  MEMORY CORE ONLINE  //  GLORY TO MANKIND  //  ",
            470,
            bar + feed_h + 24,
            550,
            22,
            10,
            MUTED,
        ),
        f'<text x="{width - 20}" y="{bar + feed_h + 24}" text-anchor="end" font-size="10" '
        f'fill="{MUTED}" letter-spacing="2">1920x620</text>',
    ]
    defs = (
        '<filter id="warm" color-interpolation-filters="sRGB">'
        '<feColorMatrix type="saturate" values=".42"/>'
        '<feComponentTransfer>'
        '<feFuncR type="linear" slope=".96" intercept=".10"/>'
        '<feFuncG type="linear" slope=".92" intercept=".09"/>'
        '<feFuncB type="linear" slope=".82" intercept=".07"/>'
        "</feComponentTransfer></filter>"
        # a photo vignette stays dark in both themes rather than punching a hole
        # in the page, so the fades run to black and never to the page colour
        f'<linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="#000" stop-opacity=".82"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="fadeBottom" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".85"/></linearGradient>'
        f'<linearGradient id="fadeLeft" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="#000" stop-opacity=".8"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="fadeRight" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".8"/></linearGradient>'
        f'<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="{GOLD}" stop-opacity="0"/><stop offset=".85" stop-color="{GOLD}" stop-opacity=".12"/>'
        f'<stop offset="1" stop-color="#f0e9d8" stop-opacity=".3"/></linearGradient>'
    )
    return svg("".join(body), width, height, f"{stats['login']} terminal feed", defs)


# ----------------------------------------------------------------- separator


def separator(number: str, label: str, width: int = 1200) -> str:
    h = 58
    body = [
        f'<rect width="{width}" height="{h}" fill="{BG}"/>',
        f'<path d="M0 29H400" stroke="{GOLD}" stroke-opacity=".28"/>',
        f'<path d="M800 29H{width}" stroke="{GOLD}" stroke-opacity=".28"/>',
        # travelling glints, clipped to the rule so the restart never shows
        '<clipPath id="railL"><rect x="0" y="26" width="400" height="6"/></clipPath>',
        '<clipPath id="railR"><rect x="800" y="26" width="400" height="6"/></clipPath>',
        f'<g clip-path="url(#railL)"><rect x="-90" y="28" width="90" height="2" fill="url(#gold)">'
        '<animate attributeName="x" values="-90;400" dur="5s" repeatCount="indefinite"/></rect></g>',
        f'<g clip-path="url(#railR)"><rect x="800" y="28" width="90" height="2" fill="url(#gold)">'
        '<animate attributeName="x" values="800;1290" dur="5s" begin="-2.5s" '
        'repeatCount="indefinite"/></rect></g>',
        f'<text x="600" y="34" text-anchor="middle" font-size="13" fill="{PAPER}" '
        f'letter-spacing="5">{esc(number)} // {esc(label)}</text>',
        f'<text x="600" y="34" text-anchor="middle" font-size="13" fill="{GOLD}" '
        f'letter-spacing="5" opacity="0">{esc(number)} // {esc(label)}'
        '<animate attributeName="opacity" values="0;0;.85;0;0" keyTimes="0;.9;.93;.96;1" '
        'dur="7s" repeatCount="indefinite"/></text>',
        # loading underline, grows from the middle
        f'<rect x="470" y="45" width="260" height="2" fill="{DIM}"/>',
        f'<rect x="600" y="45" width="0" height="2" fill="url(#gold)">'
        '<animate attributeName="width" values="0;260;260;0" dur="6s" repeatCount="indefinite"/>'
        '<animate attributeName="x" values="600;470;470;600" dur="6s" repeatCount="indefinite"/></rect>',
    ]
    return svg("".join(body), width, h, f"Section {number} // {label}")


# --------------------------------------------------------------- commit panel


def commit_panel(stats: dict, unit: str, width: int = 1200) -> str:
    height, base, max_h = 394, 304, 100
    years = stats["years"]
    peak = max(years.values()) or 1
    body = [
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
        f'<rect width="{width}" height="{height}" fill="url(#grid)"/>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="none" stroke="{GOLD}" stroke-opacity=".35"/>',
        # header
        f'<text x="24" y="26" font-size="11" fill="{GOLD}" letter-spacing="3">'
        "MEMORY ARCHIVE // COMMIT TELEMETRY</text>",
        f'<text x="{width - 24}" y="26" text-anchor="end" font-size="9" fill="{MUTED}" letter-spacing="2">'
        f'SRC: GITHUB API // {datetime.now(timezone.utc):%Y-%m-%d} // PUBLIC DATA</text>',
        f'<path d="M0 40H{width}" stroke="{GOLD}" stroke-opacity=".3"/>',
        # headline numbers
    ]

    cells = [
        ("TOTAL COMMITS", f"{stats['commits']:,}"),
        (f"COMMITS {stats['year']}", f"{stats['year_commits']:,}"),
        ("STARS EARNED", f"{stats['stars']:,}"),
        ("REPOSITORIES", f"{stats['repos']:,}"),
        ("FOLLOWERS", f"{stats['followers']:,}"),
    ]
    for index, (label, value) in enumerate(cells):
        x = 24 + index * 236
        # The plain attributes hold the final state; the animation only replays
        # it, so the panel still reads if SMIL never runs.
        k = round(0.1 * index, 3)
        bar = len(value) * 24 + 30
        body.append(
            f'<g transform="translate({x} 0)">'
            f'<text x="0" y="66" font-size="9" fill="{MUTED}" letter-spacing="2">{esc(label)}</text>'
            f'<g><animate attributeName="opacity" values="0;0;1" keyTimes="0;{k};1" '
            'dur="1.4s" fill="freeze"/>'
            '<animateTransform attributeName="transform" type="translate" values="0 9;0 9;0 0" '
            f'keyTimes="0;{k};1" dur="1.4s" fill="freeze"/>'
            f'<text x="0" y="118" font-size="40" fill="{PAPER}">{esc(value)}</text></g>'
            f'<rect x="0" y="130" width="{bar}" height="2" fill="url(#gold)" opacity=".8">'
            f'<animate attributeName="width" values="0;0;{bar}" keyTimes="0;{k};1" '
            'dur="1.4s" fill="freeze"/></rect>'
            f'<rect x="{bar + 6}" y="128" width="7" height="12" fill="{GOLD}">'
            '<animate attributeName="opacity" values="1;.1;1" dur="1.4s" '
            'begin="1.4s" repeatCount="indefinite"/></rect>'
            f"</g>"
        )
        if index:
            body.append(
                f'<path d="M{24 + index * 236 - 22} 54V132" stroke="{DIM}" stroke-dasharray="2 6"/>'
            )
    body.append(f'<path d="M0 152H{width}" stroke="{GOLD}" stroke-opacity=".3"/>')
    body.append(
        f'<text x="24" y="178" font-size="10" fill="{GOLD}" letter-spacing="3">'
        "COMMITS PER YEAR</text>"
    )

    step, bar_w = 64, 36
    for index, (year, value) in enumerate(sorted(years.items())):
        bar_h = round(value / peak * max_h)
        x = 44 + index * step
        top = base - bar_h
        k = round(0.12 + index * 0.06, 3)
        k_text = round(k + 0.06, 3)
        highlight = value == peak and value > 0
        body.append(
            f'<g>'
            f'<rect x="{x}" y="{top}" width="{bar_w}" height="{bar_h}" '
            f'fill="url(#bar)" opacity="{".95" if highlight else ".7"}">'
            f'<animate attributeName="height" values="0;0;{bar_h}" keyTimes="0;{k};1" dur="2s" fill="freeze"/>'
            f'<animate attributeName="y" values="{base};{base};{top}" keyTimes="0;{k};1" dur="2s" fill="freeze"/>'
            f"</rect>"
        )
        if value:
            body.append(
                f'<text x="{x + bar_w / 2}" y="{top - 8}" text-anchor="middle" font-size="10" fill="{PAPER}">{value}'
                f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{k_text};1" dur="2s" fill="freeze"/></text>'
            )
        body.append(
            f'<text x="{x + bar_w / 2}" y="{base + 16}" text-anchor="middle" font-size="9" '
            f'fill="{MUTED}" letter-spacing="1">{year}</text>'
            f'<rect x="{x}" y="{base}" width="{bar_w}" height="1" fill="{GOLD}" opacity=".5"/>'
            f"</g>"
        )

    # live unit feed on the right
    fx, fy, fw, fh = 790, 158, 386, 192
    ucx, ucy = fx + fw / 2, fy + fh / 2
    body.extend([
        f'<clipPath id="unit"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}"/></clipPath>'
        f'<g clip-path="url(#unit)">'
        f'<g transform="translate({ucx} {ucy})"><g>'
        '<animateTransform attributeName="transform" type="scale" values="1;1.05;1" dur="24s" '
        'calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1" '
        'repeatCount="indefinite"/>'
        f'<g transform="translate(-{ucx} -{ucy})">'
        f'<image xlink:href="data:image/jpeg;base64,{unit}" x="{fx}" y="{fy}" width="{fw}" '
        f'height="{fh}" preserveAspectRatio="xMidYMin slice" filter="url(#warm)"/>'
        "</g></g></g>"
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="url(#scan)"/>'
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="62" fill="url(#fadeTop)"/>'
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="url(#fadeBottom)"/>'
        f'<rect x="{fx}" y="{fy - 58}" width="{fw}" height="58" fill="url(#beam)" opacity=".8">'
        f'<animate attributeName="y" values="{fy - 58};{fy + fh}" dur="6s" repeatCount="indefinite"/></rect>'
        "</g>"
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="none" stroke="{GOLD}" stroke-opacity=".4"/>',
        ticks(fx, fy, fw, fh, 12, 0.8),
        f'<text x="{fx + 12}" y="{fy + fh - 12}" font-size="9" fill="{PHOTO_INK}" letter-spacing="2">'
        "VISUAL FEED // UNIT 2B</text>",
        mark(fx + fw - 46, fy + 16, 4, "#c96a5a", 1.4, 0),
        f'<text x="{fx + fw - 36}" y="{fy + 19}" font-size="9" fill="#c96a5a" letter-spacing="2">REC</text>',
        # footer
        f'<path d="M0 362H{width}" stroke="{GOLD}" stroke-opacity=".25"/>',
        f'<text x="24" y="382" font-size="9" fill="{MUTED}" letter-spacing="2">'
        "SYNC COMPLETE // MEMORY CORE STABLE</text>",
        f'<rect x="250" y="372" width="120" height="2" fill="{DIM}"/>',
        f'<rect x="250" y="372" width="34" height="2" fill="url(#gold)">'
        '<animate attributeName="x" values="250;336;250" dur="3.4s" calcMode="spline" '
        'keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1" repeatCount="indefinite"/></rect>',
        mark(388, 373, 3, GOLD, 1.2, 0),
        f'<text x="{width - 24}" y="382" text-anchor="end" font-size="9" fill="{GOLD}" letter-spacing="2">'
        f"LIVE // SINCE {min(years)}</text>",
    ])
    defs = (
        '<filter id="warm" color-interpolation-filters="sRGB">'
        '<feColorMatrix type="saturate" values=".42"/>'
        '<feComponentTransfer>'
        '<feFuncR type="linear" slope=".96" intercept=".10"/>'
        '<feFuncG type="linear" slope=".92" intercept=".09"/>'
        '<feFuncB type="linear" slope=".82" intercept=".07"/>'
        "</feComponentTransfer></filter>"
        f'<linearGradient id="fadeBottom" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".8"/></linearGradient>'
        f'<linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="#000" stop-opacity=".85"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="{GOLD}" stop-opacity="0"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".28"/></linearGradient>'
    )
    return svg("".join(body), width, height, "Live commit telemetry", defs)


# -------------------------------------------------------------------- footer


def terminal_footer(stats: dict, width: int = 1200) -> str:
    h = 120
    body = [
        f'<rect width="{width}" height="{h}" fill="{BG}"/>',
        f'<rect width="{width}" height="{h}" fill="url(#grid)"/>',
        f'<path d="M0 1H{width}" stroke="{GOLD}" stroke-opacity=".5"/>',
        f'<text x="28" y="40" font-size="13" fill="{PAPER}" letter-spacing="4">END OF TRANSMISSION</text>',
        f'<g><text x="{width - 28}" y="40" text-anchor="end" font-size="13" fill="{GOLD}" '
        'letter-spacing="4">GLORY TO MANKIND</text>'
        '<animate attributeName="opacity" values="1;1;.25;1;1" keyTimes="0;.86;.9;.94;1" '
        'dur="6s" repeatCount="indefinite"/></g>',
        f'<text x="28" y="66" font-size="9" fill="{MUTED}" letter-spacing="2">'
        f'CONNECTION TERMINATING // {stats["commits"]:,} COMMITS ARCHIVED</text>',
        f'<text x="{width - 28}" y="66" text-anchor="end" font-size="9" fill="{MUTED}" '
        'letter-spacing="2">ARCHIVE WRITE PROTECTED</text>',
        f'<rect x="28" y="86" width="{width - 56}" height="2" fill="{DIM}"/>',
        f'<rect x="28" y="86" width="0" height="2" fill="url(#gold)">'
        f'<animate attributeName="width" values="0;{width - 56};{width - 56};0" dur="8s" '
        'repeatCount="indefinite"/></rect>',
        mark(28, 104, 3, GOLD, 1.3, 0),
        f'<text x="40" y="107" font-size="9" fill="{MUTED}" letter-spacing="2">POD 042 // SHUTDOWN SEQUENCE</text>',
        f'<text x="{width - 28}" y="107" text-anchor="end" font-size="9" fill="{GOLD}" '
        'letter-spacing="3">...</text>',
    ]
    return svg("".join(body), width, h, "Terminal shutdown footer")


# --------------------------------------------------------------- status header

# abrupt on/off, never eased: a glitch has to cut, not fade
FLICKER_A = ('values="0;0;1;0;0;1;0" keyTimes="0;.7;.72;.76;.86;.88;1"', 6)
FLICKER_B = ('values="0;1;0;0;1;0" keyTimes="0;.28;.32;.74;.78;1"', 7.5)
FLICKER_C = ('values="0;0;1;0;0" keyTimes="0;.52;.54;.58;1"', 9)

CORRUPT = {"O": "0", "E": "3", "I": "1", "S": "5", "A": "4", "T": "7", "B": "8"}


def corrupt(text: str) -> str:
    return "".join(CORRUPT.get(ch, ch) if index % 3 == 0 else ch for index, ch in enumerate(text))


def status_header(width: int = 720) -> str:
    """Two lines of terminal text with a torn-slice glitch, no typing."""
    h = 58
    cx = width // 2
    rows = (
        ("SYSTEM ONLINE // WELCOME, OPERATOR", 22, 14, PAPER),
        (f"DESIGNATION: {LOGIN} // SYSTEMS DEVELOPER", 46, 13, MUTED),
    )
    body = []
    for row, (text, y, size, colour) in enumerate(rows):
        anchor = f'text-anchor="middle" font-size="{size}" letter-spacing="1.5"'
        # the base line jumps sideways for two frames
        body.append(
            f'<text x="{cx}" y="{y}" {anchor} fill="{colour}">{esc(text)}'
            '<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 0;2.5 0;0 0;0 0" keyTimes="0;{0.6 + row * .05:.2f};'
            f'{0.62 + row * .05:.2f};{0.66 + row * .05:.2f};1" '
            'dur="6.5s" repeatCount="indefinite"/></text>'
        )
        # slices of the same line, shifted and clipped to a six-pixel band
        for index, (offset, dx, ghost, spark) in enumerate(
            (
                (-12, 3.5, GOLD, FLICKER_A if row == 0 else FLICKER_B),
                (-6, -3.5, "#a1523f", FLICKER_B if row == 0 else FLICKER_A),
            )
        ):
            band = f"t{row}{index}"
            values, dur = spark
            body.append(
                f'<clipPath id="{band}"><rect x="0" y="{y + offset}" width="{width}" '
                'height="6"/></clipPath>'
                f'<g clip-path="url(#{band})">'
                f'<text x="{cx + dx}" y="{y}" {anchor} fill="{ghost}" opacity="0">{esc(text)}'
                f'<animate attributeName="opacity" {values} dur="{dur}s" repeatCount="indefinite"/>'
                "</text></g>"
            )
        values, dur = FLICKER_C
        body.append(
            f'<text x="{cx + 2.4}" y="{y}" {anchor} fill="{colour}" opacity="0">'
            f"{esc(corrupt(text))}"
            f'<animate attributeName="opacity" {values} dur="{dur + row * 1.5}s" '
            'repeatCount="indefinite"/>'
            "</text>"
        )
    return svg("".join(body), width, h, f"{LOGIN} status line")


# ------------------------------------------------------------- access counter


def counter_rail(side: str, width: int = 504) -> str:
    """Housing for the live counter: the README stacks a rail, the counter
    image (fetched by the browser, so the number is current), then a rail.
    The counter is 476 wide, so the rails sit 14px proud on each side."""
    h = 36
    left, right = {
        "top": ("ACCESS LOG", "LIVE // COUNTER NODE 01"),
        "bottom": ("ARCHIVE ACCESS COUNT", "SYNCED ON VIEW"),
    }[side]
    edge = h - 1 if side == "top" else 1
    body = [
        f'<path d="M0 {edge}H{width}" stroke="{GOLD}" stroke-opacity=".4"/>',
        f'<rect x="0" y="{edge - 1}" width="80" height="2" fill="url(#gold)">'
        f'<animate attributeName="x" values="-80;{width}" dur="7s" repeatCount="indefinite"/></rect>',
        mark(12, h / 2, 4, GOLD, 2.4, 0),
        f'<text x="24" y="{h / 2 + 4}" font-size="10" fill="{PAPER}" letter-spacing="2">'
        f"{esc(left)}</text>",
        f'<text x="{width - 14}" y="{h / 2 + 4}" text-anchor="end" font-size="9" fill="{GOLD}" '
        f'letter-spacing="2">{esc(right)}</text>',
    ]
    return svg("".join(body), width, h, f"Access counter {side} rail")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist")
    out = Path(parser.parse_args().output)
    out.mkdir(parents=True, exist_ok=True)

    stats = fetch_stats(LOGIN)
    art = {name: download(url) for name, url in IMAGES.items()}
    print("Stats:", json.dumps(stats))

    visuals = {
        "terminal-header.svg": terminal_header(art["hero"], stats),
        "status-glitch.svg": status_header(),
        "sep-systems.svg": separator("01", "SYSTEMS"),
        "sep-archive.svg": separator("02", "ARCHIVE"),
        "sep-comms.svg": separator("03", "COMMS"),
        "commit-stats.svg": commit_panel(stats, art["unit"]),
        "counter-top.svg": counter_rail("top"),
        "counter-bottom.svg": counter_rail("bottom"),
        "terminal-footer.svg": terminal_footer(stats),
    }
    for name, data in visuals.items():
        (out / name).write_text(data, encoding="utf-8")
        print(f"Generated {name} ({len(data) // 1024} KiB)")


if __name__ == "__main__":
    main()
