#!/usr/bin/env python3
"""Generate a GitHub 'Most Used Languages' animated solar-system SVG (no deps).

Fetches repos via the GitHub REST API, sums language bytes, and renders an
inclined-elliptic solar system where every planet is a language orbiting a
central supernova.
"""
import json
import math
import os
import urllib.request

USER = os.environ.get("GITHUB_USER", "FoxyLoon")
OUT = os.environ.get("GITHUB_OUTPUT_FILE", "assets/solar-system.svg")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_PLANETS = int(os.environ.get("MAX_PLANETS", "6"))

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5",
    "HTML": "#e34c26", "CSS": "#563d7c", "SCSS": "#c6538c", "C++": "#f34b7d",
    "C": "#555555", "Java": "#b07219", "Kotlin": "#A97BFF", "Go": "#00ADD8",
    "Rust": "#dea584", "Ruby": "#701516", "PHP": "#4F5D95", "Shell": "#89e051",
    "Vue": "#41b883", "Svelte": "#ff3e00", "Dockerfile": "#384d54",
    "Markdown": "#083fa1", "Astro": "#ff5a03", "CMake": "#DA3434",
}
LANG_SHORT = {
    "JavaScript": "JS", "TypeScript": "TS", "Python": "PY", "HTML": "HTML",
    "CSS": "CSS", "C++": "C++", "Shell": "SH", "Markdown": "MD",
    "Dockerfile": "DKR", "CMake": "CMK",
}


def fetch(url: str):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "solar-system-svg")
    if TOKEN:
        req.add_header("Authorization", f"token {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect() -> dict[str, int]:
    langs: dict[str, int] = {}
    page = 1
    while True:
        repos = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&sort=updated")
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("size", 0) == 0:
                continue
            try:
                data = fetch(repo["languages_url"])
            except Exception:
                continue
            for lang, b in data.items():
                langs[lang] = langs.get(lang, 0) + int(b)
        if len(repos) < 100:
            break
        page += 1
    return langs


def abbrev(name: str) -> str:
    short = LANG_SHORT.get(name)
    if short:
        return short
    letters = [c.upper() for c in name if c.isalpha()][:2]
    return "".join(letters) or name[:2].upper()


def render(top: list[tuple[str, int]], total: int) -> str:
    W, H = 880, 560
    cx, cy = W // 2, H // 2 + 20
    angle = -14
    orbit_r = [110, 160, 210, 260, 310]
    planets = top[:MAX_PLANETS]
    parts: list[str] = []
    add = parts.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated solar system of {USER} GitHub languages">')
    add('<rect width="100%" height="100%" fill="#0d1117"/>')

    # defs
    add('<defs>')
    add('<radialGradient id="nova" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#ffffff"/>'
        '<stop offset="18%" stop-color="#FFE400"/>'
        '<stop offset="45%" stop-color="#FF652F"/>'
        '<stop offset="100%" stop-color="#FF652F" stop-opacity="0"/>'
        '</radialGradient>')
    add('<filter id="fg" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="7"/></filter>')
    add('</defs>')

    # stars
    xs = [61, 137, 219, 291, 337, 419, 471, 559, 631, 713, 767, 841, 99, 519]
    ys = [61, 113, 167, 211, 263, 311, 359, 413, 461, 509, 551, 97, 481, 61]
    for i, (x, y) in enumerate(zip(xs, ys)):
        tw = ' class="tw"' if i % 3 == 0 else ''
        add(f'<circle cx="{x}" cy="{y}" r="1.1" fill="#8b949e" opacity="{0.25 + (i % 3) * 0.15:.2f}"{tw}/>')

    # header
    add(f'<text x="28" y="46" font-family="Fira Code, ui-monospace, monospace" font-size="15" letter-spacing="4" fill="#e6edf3">SOLAR SYSTEM · @{USER.upper()}</text>')

    # orbit paths (inclined ellipses) + dashed visuals
    for i, R in enumerate(orbit_r):
        ry = int(R * 0.42)
        d = f"M {cx + R},{cy} A {R},{ry} 0 1 0 {cx - R},{cy} A {R},{ry} 0 1 0 {cx + R},{cy}"
        add(f'<g transform="rotate({angle} {cx} {cy})"><ellipse cx="{cx}" cy="{cy}" rx="{R}" ry="{ry}" fill="none" stroke="#30363d" stroke-width="1.2" stroke-dasharray="6 8" opacity="0.55"/></g>')
        add(f'<path id="op{i + 1}" d="{d}" transform="rotate({angle} {cx} {cy})" fill="none" stroke="none"/>')

    # planets orbiting via animateMotion
    n = len(planets)
    for idx, (lang, b) in enumerate(planets):
        pct = round(b / total * 100, 1) if total else 0
        color = LANG_COLORS.get(lang, "#FF652F")
        short = abbrev(lang)
        R = orbit_r[idx % len(orbit_r)]
        pr = 17
        dur = 14 + idx * 5
        # starting point on path
        theta = math.radians(200 + (idx * (250 / max(n, 1))) % 360)
        px = R * math.cos(theta)
        py = R * 0.42 * math.sin(theta)
        a = math.radians(angle)
        sx = px * math.cos(a) - py * math.sin(a) + cx
        sy = px * math.sin(a) + py * math.cos(a) + cy
        lw = len(lang) * 12 * 0.62
        lx = sx + pr + 8 if sx <= cx else sx - pr - 8 - lw
        add(f'<g transform="translate({sx:.1f} {sy:.1f})">'
            f'<animateMotion dur="{dur}s" repeatCount="indefinite" rotate="0">'
            f'<mpath href="#op{idx + 1}"/></animateMotion>'
            f'<circle r="{pr}" fill="{color}" stroke="#0d1117" stroke-width="2"/>'
            f'<text y="4" text-anchor="middle" font-family="Fira Code, ui-monospace, monospace" font-size="10" font-weight="700" fill="#0d1117">{short}</text>'
            f'</g>')
        # static label near starting point (orbiting label would flip)
        add(f'<text x="{lx:.1f}" y="{sy + 4:.1f}" font-family="Fira Code, ui-monospace, monospace" font-size="12" fill="#e6edf3">{lang} {pct}%</text>')

    # supernova core
    add(f'<g transform="translate({cx} {cy})">')
    add('<circle r="96" fill="url(#nova)" filter="url(#fg)"/>')
    add('<circle r="96" fill="url(#nova)" opacity=".7">'
        '<animate attributeName="opacity" values=".45;.9;.45" dur="3.2s" repeatCount="indefinite"/>'
        '</circle>')
    add('<circle r="58" fill="none" stroke="#FFE400" stroke-width="2" opacity=".8">'
        '<animate attributeName="r" values="50;66;50" dur="3.2s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values=".8;.2;.8" dur="3.2s" repeatCount="indefinite"/>'
        '</circle>')
    add('<circle r="26" fill="#ffffff">'
        '<animate attributeName="r" values="24;28;24" dur="1.6s" repeatCount="indefinite"/>'
        '</circle>')
    # nova rays
    for k in range(8):
        a2 = math.radians(k * 45 + 22)
        x2 = 74 * math.cos(a2)
        y2 = 74 * math.sin(a2)
        add(f'<line x1="{9 * math.cos(a2):.1f}" y1="{9 * math.sin(a2):.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#FFE400" stroke-width="2.5" opacity=".85" stroke-linecap="round"/>')
    add('</g>')

    # css
    add('<style>.tw{animation:tw 2.6s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.2}50%{opacity:1}}</style>')

    # footer
    add(f'<text x="28" y="{H - 24}" font-family="Fira Code, ui-monospace, monospace" font-size="12" fill="#8b949e">planets = languages · orbit = share of code</text>')
    add(f'<text x="{W - 28}" y="{H - 24}" text-anchor="end" font-family="Fira Code, ui-monospace, monospace" font-size="12" fill="#8b949e">github.com/{USER}</text>')
    add("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    langs = collect()
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)
    top = [(k, v) for k, v in top if k not in ("Makefile", "Batchfile")][:8]
    total = sum(v for _, v in top)
    svg = render(top, total)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} with {len(top)} languages: {[f'{k} {round(v / total * 100, 1)}%' for k, v in top]}")
