#!/usr/bin/env python3
"""Generate a GitHub 'Most Used Languages' animated solar-system SVG (no deps).

Every planet is a language, planet size = share of total code, all orbiting a
central supernova on inclined ellipses. Comets fly by carrying repo names.
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


def abbrev(name: str) -> str:
    short = LANG_SHORT.get(name)
    if short:
        return short
    letters = [c.upper() for c in name if c.isalpha()][:2]
    return "".join(letters) or name[:2].upper()


def render(top: list[tuple[str, int]], total: int, repos: list[str], rng: random.Random) -> str:
    W, H = 960, 620
    cx, cy = W // 2, int(H * 0.55)
    angle = -14
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
        '<filter id="fg" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="7"/></filter></defs>')

    xs = [61, 137, 219, 291, 337, 419, 471, 559, 631, 713, 767, 841, 99, 519, 887, 63]
    ys = [61, 113, 167, 211, 263, 311, 359, 413, 461, 509, 551, 97, 481, 61, 523, 583]
    for i, (x, y) in enumerate(zip(xs, ys)):
        tw = ' class="tw"' if i % 3 == 0 else ''
        add(f'<circle cx="{x}" cy="{y}" r="1.1" fill="#8b949e" opacity="{0.25 + (i % 3) * 0.15:.2f}"{tw}/>')

    add(f'<text x="28" y="46" font-family="Fira Code, ui-monospace, monospace" font-size="15" letter-spacing="4" fill="#e6edf3">SOLAR SYSTEM · @{USER.upper()}</text>')

    n = len(top)
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))

    def orbit_ellipse(R: float) -> tuple[float, float]:
        return R * 0.40, angle  # ry factor, rotation

    # orbit visuals
    for i in range(n):
        R = 92 + i * 36
        ry = R * 0.40
        add(f'<ellipse cx="{cx}" cy="{cy}" rx="{R}" ry="{ry:.1f}" fill="none" stroke="#30363d" '
            f'stroke-width="1.2" stroke-dasharray="6 8" opacity="0.5" '
            f'transform="rotate({angle} {cx} {cy})"/>')

    # planets: every language, size = share
    for idx, (lang, b) in enumerate(top):
        pct = (b / total * 100) if total else 0
        color = LANG_COLORS.get(lang, "#FF652F")
        short = abbrev(lang)
        R = 92 + idx * 36
        ry = R * 0.40
        # inclined ellipse motion path (inline path, no mpath)
        ex, ey = cx + R * ca, cy + R * sa          # major-axis end
        bx, by = cx - R * ca, cy - R * sa
        path = (f"M {ex:.1f},{ey:.1f} A {R},{ry:.1f} {angle} 1 0 {bx:.1f},{by:.1f} "
                f"A {R},{ry:.1f} {angle} 1 0 {ex:.1f},{ey:.1f}")
        dur = 16 + idx * 4
        pr = round(6 + math.sqrt(max(pct, 0.05)) * 2.6, 1)
        pr = min(pr, 26)
        px = ex
        py = ey
        lw = len(lang) * 12 * 0.62
        lx = px + pr + 8 if px <= cx else px - pr - 8 - lw
        add(f'<g>'
            f'<animateMotion dur="{dur}s" repeatCount="indefinite" rotate="0" path="{path}"/>'
            f'<circle r="{pr}" fill="{color}" stroke="#0d1117" stroke-width="2"/>'
            f'<text y="4" text-anchor="middle" font-family="Fira Code, ui-monospace, monospace" '
            f'font-size="{max(8, round(pr * 0.55))}" font-weight="700" fill="#0d1117">{short}</text>'
            f'</g>')
        add(f'<text x="{lx:.1f}" y="{py + 4:.1f}" font-family="Fira Code, ui-monospace, monospace" '
            f'font-size="12" fill="#e6edf3">{lang} {pct:.1f}%</text>')

    # comets: random repos flying by
    comet_count = min(3, max(1, len(repos) // 2)) if repos else 2
    comet_repos = rng.sample(repos, min(comet_count, len(repos))) if repos else []
    for i in range(comet_count):
        name = comet_repos[i] if i < len(comet_repos) else f"project-{i + 1}"
        dur = rng.choice([7, 9, 11])
        delay = rng.choice([-2, -4, -5, -7])
        y0 = rng.choice([110, 160, 480, 520])
        x0, x1 = 30, W - 30
        drift = rng.choice([-60, -30, 30, 60])
        path = f"M {x0},{y0} Q {(x0 + x1) / 2},{y0 + drift} {x1},{y0 + drift}"
        add(f'<g opacity="0.9">'
            f'<animateMotion dur="{dur}s" repeatCount="indefinite" begin="{delay}s" rotate="0" path="{path}"/>'
            f'<line x1="0" y1="0" x2="-26" y2="6" stroke="#FF652F" stroke-width="2" opacity=".65" stroke-linecap="round"/>'
            f'<circle r="3" fill="#FFE400" filter="url(#fg)"/>'
            f'</g>')
        add(f'<text x="{x1 - 10}" y="{y0 + drift + rng.choice([-10, -12, -14])}" text-anchor="end" '
            f'font-family="Fira Code, ui-monospace, monospace" font-size="11" fill="#8b949e" opacity=".85">{name}</text>')

    # supernova core
    add(f'<g transform="translate({cx} {cy})">')
    add('<circle r="96" fill="url(#nova)" filter="url(#fg)"/>')
    add('<circle r="96" fill="url(#nova)" opacity=".7">'
        '<animate attributeName="opacity" values=".45;.9;.45" dur="3.2s" repeatCount="indefinite"/></circle>')
    add('<circle r="58" fill="none" stroke="#FFE400" stroke-width="2" opacity=".8">'
        '<animate attributeName="r" values="50;66;50" dur="3.2s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values=".8;.2;.8" dur="3.2s" repeatCount="indefinite"/></circle>')
    add('<circle r="26" fill="#ffffff">'
        '<animate attributeName="r" values="24;28;24" dur="1.6s" repeatCount="indefinite"/></circle>')
    for k in range(8):
        a2 = math.radians(k * 45 + 22)
        x2 = 74 * math.cos(a2)
        y2 = 74 * math.sin(a2)
        add(f'<line x1="{9 * math.cos(a2):.1f}" y1="{9 * math.sin(a2):.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#FFE400" stroke-width="2.5" opacity=".85" stroke-linecap="round"/>')
    add('</g>')

    add('<style>.tw{animation:tw 2.6s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.2}50%{opacity:1}}</style>')
    add(f'<text x="28" y="{H - 24}" font-family="Fira Code, ui-monospace, monospace" font-size="12" fill="#8b949e">planets = languages · size = share of code · comets = repos</text>')
    add(f'<text x="{W - 28}" y="{H - 24}" text-anchor="end" font-family="Fira Code, ui-monospace, monospace" font-size="12" fill="#8b949e">github.com/{USER}</text>')
    add("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    langs, repos = collect()
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)
    top = [(k, v) for k, v in top if k not in ("Makefile", "Batchfile")][:MAX_PLANETS]
    total = sum(v for _, v in top)
    rng = random.Random(42)
    svg = render(top, total, repos, rng)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}: {len(top)} languages, {len(repos)} repos")
