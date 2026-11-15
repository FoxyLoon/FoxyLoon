#!/usr/bin/env python3
"""Generate a GitHub 'Most Used Languages' animated solar-system SVG (no deps).

Every planet is a language; planet size = share of total code, the smallest
planet orbits closest to the supernova and spins fastest. Comets fly along
diagonals carrying repo names. The supernova sits under every other element.
"""
import json
import math
import os
import random
import urllib.request

USER = os.environ.get("GITHUB_USER", "FoxyLoon")
OUT = os.environ.get("GITHUB_OUTPUT_FILE", "assets/solar-system.svg")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_PLANETS = int(os.environ.get("MAX_PLANETS", "10"))

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


def collect() -> tuple[dict[str, int], list[str]]:
    langs: dict[str, int] = {}
    repos: list[str] = []
    page = 1
    while True:
        data = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&sort=updated")
        if not data:
            break
        for repo in data:
            if repo.get("fork") or repo.get("size", 0) == 0:
                continue
            repos.append(repo["name"])
            try:
                for lang, b in fetch(repo["languages_url"]).items():
                    langs[lang] = langs.get(lang, 0) + int(b)
            except Exception:
                continue
        if len(data) < 100:
            break
        page += 1
    return langs, repos


def count_all_repos() -> int:
    """Public + private repos of the authenticated user when TOKEN is set,
    otherwise the public count."""
    try:
        if TOKEN:
            total = 0
            page = 1
            while True:
                data = fetch(f"https://api.github.com/user/repos?per_page=100&visibility=all&affiliation=owner&page={page}")
                total += len(data)
                if len(data) < 100:
                    break
                page += 1
            return total
        me = fetch(f"https://api.github.com/users/{USER}")
        return int(me.get("public_repos", 0))
    except Exception:
        return 0


def abbrev(name: str) -> str:
    short = LANG_SHORT.get(name)
    if short:
        return short
    letters = [c.upper() for c in name if c.isalpha()][:2]
    return "".join(letters) or name[:2].upper()


def render(top: list[tuple[str, int]], total: int, total_repos: int, rng: random.Random) -> str:
    W, H = 960, 600
    cx, cy = W // 2, int(H * 0.52)
    angle = -14
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    parts: list[str] = []
    add = parts.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated solar system of {USER} GitHub languages">')
    add('<rect width="100%" height="100%" fill="#0d1117"/>')
    add('<defs><radialGradient id="nova" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#ffffff"/>'
        '<stop offset="18%" stop-color="#FFE400"/>'
        '<stop offset="45%" stop-color="#FF652F"/>'
        '<stop offset="100%" stop-color="#FF652F" stop-opacity="0"/>'
        '</radialGradient>'
        '<filter id="fg" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="5"/></filter></defs>')

    # stars
    xs = [61, 137, 219, 291, 337, 419, 471, 559, 631, 713, 767, 841, 99, 519, 887, 63, 901, 251]
    ys = [61, 113, 167, 211, 263, 311, 359, 413, 461, 509, 551, 97, 481, 61, 523, 583, 71, 547]
    for i, (x, y) in enumerate(zip(xs, ys)):
        tw = ' class="tw"' if i % 3 == 0 else ''
        add(f'<circle cx="{x}" cy="{y}" r="1.1" fill="#8b949e" opacity="{0.25 + (i % 3) * 0.15:.2f}"{tw}/>')

    add(f'<text x="28" y="44" font-family="Fira Code, ui-monospace, monospace" font-size="15" letter-spacing="4" fill="#e6edf3">SOLAR SYSTEM · @{USER.upper()}</text>')

    # supernova FIRST so orbits & planets render above it
    add(f'<g transform="translate({cx} {cy})">')
    add('<circle r="62" fill="url(#nova)" filter="url(#fg)"/>')
    add('<circle r="62" fill="url(#nova)" opacity=".7">'
        '<animate attributeName="opacity" values=".45;.9;.45" dur="3.2s" repeatCount="indefinite"/></circle>')
    add('<circle r="38" fill="none" stroke="#FFE400" stroke-width="2" opacity=".8">'
        '<animate attributeName="r" values="32;44;32" dur="3.2s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values=".8;.2;.8" dur="3.2s" repeatCount="indefinite"/></circle>')
    add('<circle r="16" fill="#ffffff">'
        '<animate attributeName="r" values="14;18;14" dur="1.6s" repeatCount="indefinite"/></circle>')
    for k in range(8):
        a2 = math.radians(k * 45 + 22)
        x2 = 46 * math.cos(a2)
        y2 = 46 * math.sin(a2)
        add(f'<line x1="{8 * math.cos(a2):.1f}" y1="{8 * math.sin(a2):.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#FFE400" stroke-width="2" opacity=".85" stroke-linecap="round"/>')
    add('</g>')

    # orbits (bigger radii, more spacing)
    n = len(top)
    for i in range(n):
        R = 140 + i * 62
        ry = R * 0.42
        add(f'<ellipse cx="{cx}" cy="{cy}" rx="{R}" ry="{ry:.1f}" fill="none" stroke="#30363d" '
            f'stroke-width="1.2" stroke-dasharray="6 8" opacity="0.5" '
            f'transform="rotate({angle} {cx} {cy})"/>')

    # planets: smallest first = closest to the supernova = fastest
    ordered = sorted(top, key=lambda kv: kv[1])
    for idx, (lang, b) in enumerate(ordered):
        pct = (b / total * 100) if total else 0
        color = LANG_COLORS.get(lang, "#FF652F")
        short = abbrev(lang)
        R = 140 + idx * 62
        ry = R * 0.42
        ex, ey = cx + R * ca, cy + R * sa
        bx, by = cx - R * ca, cy - R * sa
        path = (f"M {ex:.1f},{ey:.1f} A {R},{ry:.1f} {angle} 1 0 {bx:.1f},{by:.1f} "
                f"A {R},{ry:.1f} {angle} 1 0 {ex:.1f},{ey:.1f}")
        dur = min(30.0, max(8.0, 8.0 + pct * 0.45))
        pr = round(6 + math.sqrt(max(pct, 0.05)) * 2.6, 1)
        pr = min(pr, 26)
        add(f'<g>'
            f'<animateMotion dur="{dur:.1f}s" repeatCount="indefinite" rotate="0" path="{path}"/>'
            f'<circle r="{pr}" fill="{color}" stroke="#0d1117" stroke-width="2"/>'
            f'<text y="4" text-anchor="middle" font-family="Fira Code, ui-monospace, monospace" '
            f'font-size="{max(8, round(pr * 0.55))}" font-weight="700" fill="#0d1117">{short}</text>'
            f'</g>')

    # comets: one per repo (public + private), anonymous, 45-degree diagonals
    # starting along the top edge or the left edge, heading lower-right
    for i in range(total_repos):
        top_edge = i % 2 == 0
        if top_edge:
            x0, y0 = 40 + rng.randint(0, W - 120), 30
        else:
            x0, y0 = 30, 70 + rng.randint(0, 180)
        x1, y1 = W - 20, min(H - 50, y0 + (W - 20 - x0))
        dur = rng.uniform(6, 12)
        delay = -(i * 1.7 % 14)
        add(f'<g opacity="0.9">'
            f'<animateMotion dur="{dur:.1f}s" repeatCount="indefinite" begin="{delay:.1f}s" rotate="auto" path="M {x0},{y0} L {x1},{y1}"/>'
            f'<line x1="0" y1="0" x2="-24" y2="0" stroke="#FF652F" stroke-width="2" opacity=".7" stroke-linecap="round"/>'
            f'<circle r="3" fill="#FFE400" filter="url(#fg)"/>'
            f'</g>')

    add('<style>.tw{animation:tw 2.6s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.2}50%{opacity:1}}</style>')
    add(f'<text x="28" y="{H - 24}" font-family="Fira Code, ui-monospace, monospace" font-size="12" fill="#8b949e">planets = languages</text>')
    add(f'<text x="{W - 28}" y="{H - 24}" text-anchor="end" font-family="Fira Code, ui-monospace, monospace" font-size="12" fill="#8b949e">github.com/{USER}</text>')
    add("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    langs, repos = collect()
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)
    top = [(k, v) for k, v in top if k not in ("Makefile", "Batchfile")][:MAX_PLANETS]
    total = sum(v for _, v in top)
    total_repos = count_all_repos()
    rng = random.Random(42)
    svg = render(top, total, total_repos, rng)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}: {len(top)} languages, {total_repos} comets")
