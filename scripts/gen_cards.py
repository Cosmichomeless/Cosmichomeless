#!/usr/bin/env python3
"""Genera las tarjetas SVG de proyectos del README del perfil.

Cada tarjeta replica la del portfolio (iamcosmic.dev): ilustración animada,
nombre, estado, tipo, descripción, tecnologías y enlace. GitHub no permite CSS
ni JS en un README, pero sí imágenes SVG (con animaciones CSS internas).

Uso:  python3 scripts/gen_cards.py     (escribe en ../projects/*.svg)
"""
import math
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "projects"

W = 280            # ancho de la tarjeta
VIS_H = 104        # alto de la zona de la ilustración
PAD = 16           # margen interior del cuerpo
DESC_COLS = 38     # caracteres por línea de la frase corta (conservador)
MAX_TECH = 4       # etiquetas de tecnología por tarjeta
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

BG, FG, MUTED, DIM = "#232329", "#ededef", "#a1a1aa", "#71717a"

# ── Datos (los mismos que src/lib/data.ts del portfolio, versión en inglés) ──
REPOS = [
    dict(file="forge", title="FORGE", visual="kanban", hue="#f2cc60", repo="FORGE",
         type="Full-stack SaaS", status="v1.0.0 · live demo",
         desc="Project management for small teams, inspired by Linear and Jira: organizations with roles, projects, issues, comments and an activity history.",
         tech=["Java", "Spring Boot", "Next.js", "PostgreSQL", "Docker"]),
    dict(file="queuelab", title="QueueLab", visual="queue", hue="#2dd4bf", repo="QueueLab",
         type="Backend · Distributed systems", status="v1.0.0 · local only",
         desc="Async job platform: a REST API queues jobs in RabbitMQ, an independent worker processes them and stores the result, and a dashboard shows their status.",
         tech=["Java", "Spring Boot", "RabbitMQ", "PostgreSQL", "Next.js", "Docker"]),
    dict(file="syncpad", title="SyncPad", visual="sync", hue="#60a5fa", repo="SyncPad",
         type="Real-time · Offline-first", status="v1.0.0 · live demo",
         desc="Collaborative notes workspace that works in real time and offline, focused on resolving conflicts when two clients edit at once.",
         tech=["Next.js", "TypeScript", "WebSockets", "CRDTs"]),
    dict(file="tab", title="TAB", visual="split", hue="#0b9486", repo="TAB",
         type="iOS app · Offline-first", status="v1.0.0 · local demo",
         desc="Offline expense splitting with SQLite, balances and safe editing; the sync engine is tested without a public backend.",
         tech=["Swift", "SwiftUI", "SQLite", "Supabase"]),
    dict(file="stride", title="STRIDE", visual="route", hue="#e8284e", repo="STRIDE",
         type="iOS app · GPS", status="v1.0.0 · local demo",
         desc="Native running tracker focused on reliable GPS: background location, data filtering, MapKit routes and persistent sessions.",
         tech=["Swift", "SwiftUI", "CoreLocation", "MapKit", "SwiftData"]),
    dict(file="murmur", title="MURMUR", visual="wave", hue="#7a3ed6", repo="MURMUR",
         type="iOS app · Audio", status="v0.1.0 · local demo",
         desc="Voice notes with a real-time waveform: audio capture, buffers, audio session lifecycle and local persistence.",
         tech=["Swift", "SwiftUI", "AVFoundation", "SwiftData"]),
    dict(file="receipt-scanner", title="Receipt Scanner", visual="receipt", hue="#2567ec", repo="RECEIPT-SCANNER",
         type="iOS app · OCR", status="v1.0.0 · local demo",
         desc="On-device receipt scanner: turns noisy OCR text into merchant, date, amount and currency with heuristic parsing.",
         tech=["Swift", "SwiftUI", "Vision", "VisionKit", "SwiftData"]),
    dict(file="atlas-ai", title="Atlas AI", visual="rag", hue="#22d3ee", repo="Atlas-AI",
         type="AI · RAG", status="v1.0.1 · local demo",
         desc="Q&A over your documents with embeddings and semantic search, returning answers with citations to the original content.",
         tech=["Python", "FastAPI", "PostgreSQL", "pgvector"]),
    dict(file="magictap", title="MagicTap", visual="mouse", hue="#fb923c", repo="magictap",
         type="macOS app · Gestures", status="v0.2.2 · DMG on GitHub",
         desc="Tap to click for the Magic Mouse, which macOS only offers on trackpads: a menu bar app that recognises taps, swipes and pinches and turns them into clicks and system gestures.",
         tech=["Swift", "SwiftUI", "AppKit", "Multitouch"]),
    dict(file="tesela", title="tesela", visual="tiles", hue="#ff9e64", repo="tesela",
         type="CLI tool · macOS", status="v0.1.0 · Python script",
         desc="A terminal file manager with Finder-style icon tiles and real previews of PDFs, images, video and code: it uses Ghostty’s graphics protocol and keeps the UI smooth by computing everything on background threads.",
         tech=["Python", "Terminal", "NSWorkspace", "Kitty graphics"]),
]

BARS = [10, 18, 30, 22, 40, 56, 34, 62, 48, 26, 44, 66, 38, 20, 32, 52, 28, 16, 24, 12, 8, 6, 6, 6]

# Frase corta de cada tarjeta compacta (clave = fichero)
SHORT = {
    "forge": "Project management for small teams, inspired by Linear and Jira.",
    "queuelab": "Async jobs: REST API, RabbitMQ and a worker, with a status dashboard.",
    "syncpad": "Real-time collaborative notes that also work offline.",
    "tab": "Offline expense splitting with SQLite, balances and safe editing.",
    "stride": "Running tracker with reliable background GPS and MapKit routes.",
    "murmur": "Voice notes with a real-time waveform and local persistence.",
    "receipt-scanner": "On-device receipt OCR: merchant, date, amount and currency.",
    "atlas-ai": "Q&A over your documents with semantic search and cited answers.",
    "magictap": "Tap to click for the Magic Mouse, as a macOS menu bar app.",
    "tesela": "Finder-style tile file manager for the terminal, with real previews.",
}


def visual(kind: str) -> str:
    """Cuerpo de la ilustración (viewBox 240x120), igual que RepoVisual.tsx."""
    if kind == "queue":
        return """
<rect x="8" y="44" width="30" height="32" rx="6"/><path d="M16 56h14M16 64h9" opacity=".5"/>
<path class="rv-flow" d="M38 60h18"/>
<rect x="58" y="46" width="12" height="28" rx="3" fill="currentColor" fill-opacity=".15"/>
<rect x="74" y="46" width="12" height="28" rx="3" fill="currentColor" fill-opacity=".3"/>
<rect x="90" y="46" width="12" height="28" rx="3" fill="currentColor" fill-opacity=".5"/>
<path class="rv-flow" d="M102 60h28"/><circle cx="146" cy="60" r="14"/>
<circle cx="146" cy="60" r="5" fill="currentColor" fill-opacity=".4"/>
<path class="rv-flow" d="M160 60h28"/><path d="M190 48v26a17 6 0 0 0 34 0V48"/>
<ellipse cx="207" cy="48" rx="17" ry="6" fill="currentColor" fill-opacity=".15"/>"""
    if kind == "kanban":
        cols = "".join(
            f'<g><rect x="{x}" y="14" width="68" height="92" rx="6" opacity=".55"/><path d="M{x + 8} 24h24"/></g>'
            for x in (14, 86, 158))
        return cols + """
<rect x="20" y="34" width="56" height="16" rx="3" fill="currentColor" fill-opacity=".12"/>
<rect x="20" y="56" width="56" height="16" rx="3" fill="currentColor" fill-opacity=".12"/>
<rect x="20" y="78" width="56" height="16" rx="3" fill="currentColor" fill-opacity=".12"/>
<rect x="92" y="34" width="56" height="16" rx="3" fill="currentColor" fill-opacity=".12"/>
<rect class="rv-float" x="92" y="56" width="56" height="16" rx="3" fill="currentColor" fill-opacity=".4"/>
<rect x="164" y="34" width="56" height="16" rx="3" fill="currentColor" fill-opacity=".12"/>"""
    if kind == "sync":
        widths = [52, 64, 40, 58, 30]
        lines = "".join(
            f'<rect x="28" y="{y}" width="{widths[i]}" height="4" rx="2" fill="currentColor" fill-opacity=".25" stroke="none"/>'
            f'<rect x="148" y="{y}" width="{widths[i]}" height="4" rx="2" fill="currentColor" fill-opacity=".25" stroke="none"/>'
            for i, y in enumerate((30, 42, 54, 66, 78)))
        return f"""
<rect x="18" y="16" width="84" height="88" rx="6"/><rect x="138" y="16" width="84" height="88" rx="6"/>
{lines}
<path class="rv-flow" d="M108 50h24M132 72h-24"/>
<polygon class="rv-float" points="60,48 60,62 64,58 69,66 72,64 67,56 73,55" fill="currentColor"/>
<polygon points="180,70 180,84 184,80 189,88 192,86 187,78 193,77" fill="currentColor" fill-opacity=".55"/>"""
    if kind == "split":
        people = "".join(
            f'<g><circle cx="{x}" cy="94" r="12" fill="currentColor" fill-opacity=".12"/>'
            f'<circle cx="{x}" cy="91" r="3.5"/><path d="M{x - 6} 100a6 5 0 0 1 12 0"/></g>'
            for x in (50, 120, 190))
        return f"""
<rect x="90" y="10" width="60" height="30" rx="8" fill="currentColor" fill-opacity=".12"/>
<circle cx="104" cy="25" r="6"/><path d="M116 22h22M116 29h14" opacity=".6"/>
<path class="rv-flow" d="M120 40v22M120 62H50v20M120 62h70v20M120 62v20"/>
{people}"""
    if kind == "route":
        return """
<path d="M0 40h240M0 80h240M60 0v120M120 0v120M180 0v120" opacity=".18"/>
<path class="rv-draw" stroke-width="3" d="M20 96C50 96 50 50 84 56S130 100 160 70 196 28 222 30"/>
<circle cx="20" cy="96" r="4.5" fill="currentColor"/>
<circle cx="222" cy="30" r="8"/><circle cx="222" cy="30" r="3" fill="currentColor"/>"""
    if kind == "wave":
        bars = "".join(
            f'<rect class="rv-bar" style="animation-delay:{(i % 8) * 0.12:.2f}s" x="{14 + i * 9}" y="{60 - h / 2:g}" '
            f'width="5" height="{h}" rx="2.5" fill="currentColor" fill-opacity="{0.85 if i < 19 else 0.3}" stroke="none"/>'
            for i, h in enumerate(BARS))
        return bars + '<circle cx="14" cy="14" r="4" fill="currentColor" class="rv-float"/><path d="M180 8v104" opacity=".5"/>'
    if kind == "receipt":
        lens = [40, 54, 30, 48, 36]
        rows = "".join(f'<path d="M90 {y}h{lens[i]}" opacity=".5"/>' for i, y in enumerate((22, 34, 46, 58, 70)))
        return f"""
<path d="M80 10h80v98l-8-6-8 6-8-6-8 6-8-6-8 6-8-6-8 6-8-6-8 6z" fill="currentColor" fill-opacity=".08"/>
{rows}
<path d="M90 86h60" stroke-width="3"/>
<path d="M62 24V8h16M178 24V8h-16M62 96v16h16M178 96v16h-16" stroke-width="2"/>
<rect class="rv-scan" x="66" y="8" width="108" height="2.5" rx="1" fill="currentColor" stroke="none"/>"""
    if kind == "rag":
        docs = "".join(
            f'<g><rect x="10" y="{y}" width="40" height="28" rx="4" fill="currentColor" fill-opacity=".1"/>'
            f'<path d="M17 {y + 9}h24M17 {y + 17}h16" opacity=".5"/></g>' for y in (18, 46, 74))
        dots = "".join(
            f'<circle cx="{cx}" cy="{cy}" r="3" fill="currentColor" fill-opacity=".35" stroke="none"/>'
            for cx, cy in ((112, 46), (126, 74), (104, 78), (136, 52)))
        return f"""{docs}
<path class="rv-flow" d="M50 32L96 56M50 60h46M50 88L96 66"/>
{dots}
<circle cx="116" cy="62" r="4" fill="currentColor"/><circle cx="116" cy="62" r="13" stroke-dasharray="3 3"/>
<path class="rv-flow" d="M132 62h40"/><rect x="176" y="30" width="54" height="60" rx="6"/>
<path d="M184 44h38M184 54h30M184 64h34" opacity=".5"/>
<rect x="184" y="74" width="16" height="9" rx="3" fill="currentColor" stroke="none"/>"""
    if kind == "mouse":
        return """
<rect x="44" y="24" width="152" height="72" rx="36" fill="currentColor" fill-opacity=".08"/>
<path d="M70 60h8" opacity=".35"/><path class="rv-flow" d="M92 60h44M128 52l8 8-8 8"/>
<circle cx="156" cy="48" r="5" fill="currentColor" fill-opacity=".5" stroke="none"/>
<circle class="rv-float" cx="168" cy="64" r="5" fill="currentColor" stroke="none"/>
<circle cx="168" cy="64" r="12" stroke-dasharray="3 3"/><circle cx="168" cy="64" r="20" opacity=".35"/>
<path d="M204 40a30 30 0 0 1 0 40M214 30a44 44 0 0 1 0 60" opacity=".4"/>"""
    if kind == "tiles":
        return """
<rect x="16" y="24" width="30" height="30" rx="7"/><rect x="54" y="24" width="30" height="30" rx="7"/>
<rect x="92" y="24" width="30" height="30" rx="7" fill="currentColor" fill-opacity=".22"/>
<rect x="16" y="64" width="30" height="30" rx="7" opacity=".5"/><rect x="54" y="64" width="30" height="30" rx="7" opacity=".5"/>
<rect x="92" y="64" width="30" height="30" rx="7" opacity=".5"/>
<path d="M22 36h12M22 43h7M60 36h12M60 43h7M98 36h12M98 43h7" opacity=".45"/>
<path d="M134 20v80" stroke-dasharray="3 3" opacity=".35"/>
<rect x="146" y="24" width="78" height="46" rx="6"/>
<path class="rv-flow" d="M152 62l17-17 12 12 10-8 22 18"/>
<circle class="rv-float" cx="206" cy="38" r="5" fill="currentColor" fill-opacity=".5" stroke="none"/>
<path d="M146 82h54M146 90h38M146 98h46" opacity=".5"/>"""
    raise ValueError(kind)


CSS = """
.rv-flow{stroke-dasharray:4 4;animation:rv-dash 1.2s linear infinite}
.rv-draw{stroke-dasharray:320;stroke-dashoffset:320;animation:rv-draw 3.2s ease-in-out infinite}
.rv-bar{transform-box:fill-box;transform-origin:center;animation:rv-bar 1.1s ease-in-out infinite alternate}
.rv-scan{animation:rv-scan 2.6s ease-in-out infinite alternate}
.rv-float{animation:rv-float 2.4s ease-in-out infinite alternate}
@keyframes rv-dash{to{stroke-dashoffset:-16}}
@keyframes rv-draw{0%{stroke-dashoffset:320}60%,100%{stroke-dashoffset:0}}
@keyframes rv-bar{from{transform:scaleY(.45)}to{transform:scaleY(1)}}
@keyframes rv-scan{from{transform:translateY(0)}to{transform:translateY(100px)}}
@keyframes rv-float{from{transform:translateY(0)}to{transform:translateY(-4px)}}
@media (prefers-reduced-motion:reduce){.rv-flow,.rv-draw,.rv-bar,.rv-scan,.rv-float{animation:none}.rv-draw{stroke-dashoffset:0}}
"""


def readable(hue: str) -> str:
    """Tono para texto pequeño: si el color es oscuro lo aclara hacia el blanco."""
    r, g, b = (int(hue[i:i + 2], 16) for i in (1, 3, 5))
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    k = 0 if lum >= 0.62 else min(0.55, (0.62 - lum) * 1.1)
    return "#%02x%02x%02x" % tuple(round(c + (255 - c) * k) for c in (r, g, b))


def chip_rows(tech, max_w):
    """Reparte las etiquetas en filas; devuelve [[(texto, x, ancho)]]."""
    rows, row, x = [], [], 0
    for t in tech:
        w = len(t) * 6.0 + 14
        if row and x + w > max_w:
            rows.append(row)
            row, x = [], 0
        row.append((t, x, w))
        x += w + 5
    rows.append(row)
    return rows


def layout(r):
    lines = textwrap.wrap(SHORT[r["file"]], DESC_COLS)
    chips = chip_rows(r["tech"][:MAX_TECH], W - 2 * PAD)
    return lines, chips


def body_height(r):
    lines, chips = layout(r)
    return 32 + 18 + 24 + len(lines) * 17 + 10 + len(chips) * 25 + 8


def card(r, body_h):
    lines, chips = layout(r)
    hue = r["hue"]
    ink = readable(hue)          # color del texto pequeño (más claro si el tono es oscuro)
    H = VIS_H + body_h
    version = r["status"].split(" · ")[0]
    pill_w = len(version) * 6.2 + 26
    y_name = VIS_H + 30
    y_type = y_name + 20
    y_desc = y_type + 24
    y_chips = y_desc + (len(lines) - 1) * 17 + 14

    chip_svg = []
    for ri, row in enumerate(chips):
        cy = y_chips + ri * 25
        for t, x, w in row:
            chip_svg.append(
                f'<rect x="{PAD + x:.1f}" y="{cy}" width="{w:.1f}" height="19" rx="5" fill="#fff" fill-opacity=".05" '
                f'stroke="#fff" stroke-opacity=".10"/>'
                f'<text x="{PAD + x + w / 2:.1f}" y="{cy + 13}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{MUTED}">{escape(t)}</text>')
    desc_svg = "".join(
        f'<text x="{PAD}" y="{y_desc + i * 17}" font-family="{SANS}" font-size="12" fill="{MUTED}">{escape(l)}</text>'
        for i, l in enumerate(lines))
    vis_scale = 0.8
    vx, vy = (W - 240 * vis_scale) / 2, (VIS_H - 120 * vis_scale) / 2

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(r['title'])} — {escape(r['type'])}">
<title>{escape(r['title'])} — {escape(r['type'])} ({escape(r['status'])})</title>
<style>{CSS}</style>
<defs>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
    <path d="M20 0H0V20" fill="none" stroke="#fff" stroke-opacity=".10"/>
  </pattern>
  <radialGradient id="glow" cx="50%" cy="120%" r="75%">
    <stop offset="0" stop-color="{hue}" stop-opacity=".24"/><stop offset="1" stop-color="{hue}" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="{hue}" flood-opacity=".4"/>
  </filter>
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{VIS_H}" fill="url(#grid)"/>
  <rect width="{W}" height="{VIS_H}" fill="url(#glow)"/>
  <path d="M0 {VIS_H}H{W}" stroke="#fff" stroke-opacity=".10"/>
</g>
<g transform="translate({vx:g} {vy:g}) scale({vis_scale})" color="{hue}" fill="none" stroke="currentColor"
   stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" filter="url(#soft)">{visual(r['visual'])}</g>
<text x="{PAD}" y="{y_name}" font-family="{MONO}" font-size="14.5" font-weight="600" fill="{FG}">{escape(r['title'])}</text>
<g>
  <rect x="{W - PAD - pill_w:.1f}" y="{y_name - 14}" width="{pill_w:.1f}" height="20" rx="10" fill="{hue}" fill-opacity=".10" stroke="{hue}" stroke-opacity=".45"/>
  <circle cx="{W - PAD - pill_w + 11:.1f}" cy="{y_name - 4}" r="2.5" fill="{hue}"/>
  <text x="{W - PAD - pill_w + 19:.1f}" y="{y_name}" font-family="{MONO}" font-size="10" fill="{ink}">{escape(version)}</text>
</g>
<text x="{PAD}" y="{y_type}" font-family="{MONO}" font-size="10" letter-spacing=".6" fill="{ink}">{escape(r['type'].upper())}</text>
{desc_svg}
{''.join(chip_svg)}
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#fff" stroke-opacity=".12"/>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Las tarjetas de cada fila de tres comparten alto (el del contenido más largo).
    for i in range(0, len(REPOS), 3):
        row = REPOS[i:i + 3]
        body_h = max(body_height(r) for r in row)
        for r in row:
            (OUT / f"{r['file']}.svg").write_text(card(r, body_h), encoding="utf-8")
    print(f"{len(REPOS)} tarjetas compactas generadas en {OUT}")


if __name__ == "__main__":
    main()
