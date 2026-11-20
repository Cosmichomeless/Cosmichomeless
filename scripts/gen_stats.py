#!/usr/bin/env python3
"""Genera stats/github-stats.svg: tarjeta de estadísticas del perfil.

Sustituye a github-readme-stats (servicio externo) y usa el mismo estilo que
las tarjetas de proyectos. Los datos salen de la API GraphQL de GitHub con `gh`
(en la Action se autentica solo con GITHUB_TOKEN).

Uso:  python3 scripts/gen_stats.py [usuario]     (por defecto: Cosmichomeless)
"""
import json
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "Cosmichomeless"
OUT = Path(__file__).resolve().parent.parent / "stats" / "github-stats.svg"

W, H = 700, 236
ACCENT = "#f2cc60"
BG, FG, MUTED, DIM = "#232329", "#ededef", "#a1a1aa", "#71717a"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

QUERY = """
query($l:String!){ user(login:$l){
  followers{totalCount} pullRequests{totalCount} issues{totalCount}
  contributionsCollection{ totalCommitContributions }
  repositories(ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC, first:100){
    totalCount
    nodes{ stargazerCount languages(first:8, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name color } } } }
  }
} }"""


def fetch():
    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"l={LOGIN}"],
        check=True, capture_output=True, text=True).stdout
    return json.loads(out)["data"]["user"]


def summarize(u):
    repos = u["repositories"]["nodes"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]
            cur = langs.setdefault(n["name"], {"size": 0, "color": n["color"] or "#8b8b8b"})
            cur["size"] += e["size"]
    total = sum(v["size"] for v in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1]["size"])[:5]
    return {
        "stats": [
            ("Public repositories", u["repositories"]["totalCount"]),
            ("Stars earned", sum(r["stargazerCount"] for r in repos)),
            ("Commits (last year)", u["contributionsCollection"]["totalCommitContributions"]),
            ("Pull requests", u["pullRequests"]["totalCount"]),
            ("Issues", u["issues"]["totalCount"]),
            ("Followers", u["followers"]["totalCount"]),
        ],
        "langs": [(n, v["color"], v["size"] / total * 100) for n, v in top],
    }


def render(d):
    rows = []
    for i, (label, value) in enumerate(d["stats"]):
        y = 92 + i * 26
        rows.append(
            f'<circle cx="34" cy="{y - 4}" r="3" fill="{ACCENT}"/>'
            f'<text x="48" y="{y}" font-family="{SANS}" font-size="13.5" fill="{MUTED}">{escape(label)}</text>'
            f'<text x="316" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" font-weight="600" fill="{FG}">{value:,}</text>')

    # barra apilada de lenguajes (ancho 296 desde x=372) y leyenda
    bar_x, bar_w = 372.0, 296.0
    bar, legend, x = [], [], bar_x
    for i, (name, color, pct) in enumerate(d["langs"]):
        w = bar_w * pct / sum(p for _, _, p in d["langs"])
        bar.append(f'<rect x="{x:.1f}" y="70" width="{w:.1f}" height="9" fill="{color}"/>')
        x += w
        y = 106 + i * 26
        legend.append(
            f'<circle cx="378" cy="{y - 4}" r="4.5" fill="{color}"/>'
            f'<text x="392" y="{y}" font-family="{SANS}" font-size="13.5" fill="{MUTED}">{escape(name)}</text>'
            f'<text x="668" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12.5" fill="{FG}">{pct:.1f}%</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats for {escape(LOGIN)}">
<title>GitHub stats for {escape(LOGIN)}</title>
<defs>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  <clipPath id="bar"><rect x="{bar_x}" y="70" width="{bar_w}" height="9" rx="4.5"/></clipPath>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
    <path d="M24 0H0V24" fill="none" stroke="#fff" stroke-opacity=".06"/>
  </pattern>
  <radialGradient id="glow" cx="50%" cy="130%" r="80%">
    <stop offset="0" stop-color="{ACCENT}" stop-opacity=".16"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
  </radialGradient>
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
</g>
<text x="28" y="44" font-family="{MONO}" font-size="16" font-weight="600" fill="{FG}">GitHub stats</text>
<text x="372" y="44" font-family="{MONO}" font-size="11" letter-spacing=".66" fill="{ACCENT}">TOP LANGUAGES</text>
<path d="M28 58H316M372 58H668" stroke="#fff" stroke-opacity=".10"/>
{''.join(rows)}
<g clip-path="url(#bar)">{''.join(bar)}</g>
{''.join(legend)}
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#fff" stroke-opacity=".12"/>
</svg>
"""


def main():
    d = summarize(fetch())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(d), encoding="utf-8")
    print(f"escrito {OUT} · " + ", ".join(f"{k}={v}" for k, v in d["stats"]))


if __name__ == "__main__":
    main()
