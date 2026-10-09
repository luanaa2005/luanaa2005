#!/usr/bin/env python3
"""Generate a Star Wars-themed spaceship contribution SVG animation."""
import os
import random
import requests

TOKEN    = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ.get("GITHUB_USER", "luanaa2005")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays { contributionCount date }
        }
      }
    }
  }
}
"""


def fetch_weeks():
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def cell_color(count: int) -> str:
    if count == 0:   return "#161b22"
    if count <= 2:   return "#1a3340"
    if count <= 5:   return "#1e4a6e"
    if count <= 10:  return "#2563a8"
    return "#FFD700"


def generate_svg(weeks: list) -> str:
    CELL, GAP = 11, 3
    STEP = CELL + GAP
    PX, PY = 24, 20

    nw = len(weeks)
    W  = PX * 2 + nw * STEP
    H  = PY * 2 + 7 * STEP + 20

    # ship flies through the vertical centre of the grid
    SY = PY + 3 * STEP + CELL // 2

    # reproducible stars
    rng = random.Random(42)
    stars = [
        (rng.randint(0, W), rng.randint(0, H),
         round(rng.uniform(0.4, 1.3), 2),
         round(rng.uniform(1.2, 4.0), 2))
        for _ in range(130)
    ]

    out = []
    a = out.append

    a(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">')
    a('<defs><style>')
    a(f'.ship{{animation:fly 10s linear infinite}}')
    a('.star{animation:twinkle 2.5s ease-in-out infinite alternate}')
    a('.eng{animation:pulse .25s ease-in-out infinite alternate}')
    a('.laser{animation:laserp .15s ease-in-out infinite alternate}')
    a(f'@keyframes fly{{0%{{transform:translateX(-80px)}}100%{{transform:translateX({W+80}px)}}}}')
    a('@keyframes twinkle{0%{opacity:.15}100%{opacity:.85}}')
    a('@keyframes pulse{0%{opacity:.6}100%{opacity:1}}')
    a('@keyframes laserp{0%{opacity:.5}100%{opacity:1}}')
    a('</style>')

    a('<linearGradient id="trail" x1="0" y1="0" x2="1" y2="0">')
    a('  <stop offset="0%" stop-color="#4FC3F7" stop-opacity="0"/>')
    a('  <stop offset="100%" stop-color="#4FC3F7" stop-opacity=".65"/>')
    a('</linearGradient>')

    a('<filter id="glow" x="-40%" y="-40%" width="180%" height="180%">')
    a('  <feGaussianBlur stdDeviation="2.5" result="b"/>')
    a('  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>')
    a('</filter>')
    a('</defs>')

    # background
    a(f'<rect width="{W}" height="{H}" fill="#080812"/>')

    # stars
    for i, (sx, sy, sr, sd) in enumerate(stars):
        a(f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="white" opacity=".6" class="star" '
          f'style="animation-delay:{sd:.2f}s;animation-duration:{2+sd*.25:.1f}s"/>')

    # contribution grid
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            x = PX + wi * STEP
            y = PY + di * STEP
            a(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{cell_color(day["contributionCount"])}"/>')

    # ── spaceship ──────────────────────────────────────────────
    # all y-coords are absolute; the group's translateX drives the motion
    a('<g class="ship">')

    # exhaust trail
    a(f'<rect x="-78" y="{SY-2}" width="70" height="4" fill="url(#trail)" rx="2"/>')

    # engine glow
    a(f'<ellipse cx="-14" cy="{SY}" rx="5" ry="3" fill="#FF6B35" class="eng" filter="url(#glow)"/>')
    a(f'<ellipse cx="-19" cy="{SY}" rx="2.5" ry="1.5" fill="#FFD700" class="eng"/>')

    # main fuselage  (nose at +16, tail at -12)
    a(f'<polygon points="16,{SY} -12,{SY-5} -14,{SY} -12,{SY+5}" fill="#4FC3F7" filter="url(#glow)"/>')

    # top wing
    a(f'<polygon points="-4,{SY-5} -14,{SY-14} -16,{SY-6} -8,{SY-5}" fill="#87CEEB"/>')

    # bottom wing
    a(f'<polygon points="-4,{SY+5} -14,{SY+14} -16,{SY+6} -8,{SY+5}" fill="#87CEEB"/>')

    # cockpit
    a(f'<circle cx="7" cy="{SY-2}" r="3" fill="#0a1628"/>')
    a(f'<circle cx="7" cy="{SY-2}" r="1.8" fill="#4FC3F7" opacity=".35"/>')

    # laser beam
    a(f'<line x1="16" y1="{SY}" x2="65" y2="{SY}" '
      f'stroke="#FFD700" stroke-width="1.5" class="laser" filter="url(#glow)"/>')

    a('</g>')
    a('</svg>')

    return "\n".join(out)


if __name__ == "__main__":
    print(f"Fetching contributions for {USERNAME}…")
    weeks = fetch_weeks()
    print(f"  {len(weeks)} weeks received")

    svg = generate_svg(weeks)

    os.makedirs("dist", exist_ok=True)
    for name in ("github-contribution-grid-spaceship.svg",
                 "github-contribution-grid-spaceship-dark.svg"):
        path = f"dist/{name}"
        with open(path, "w") as fh:
            fh.write(svg)
        print(f"  wrote {path}")

    print("Done.")
