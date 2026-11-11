"""Pannelli SVG animati di Sales Gym, senza dipendenze: si aprono in Obsidian (![[x.svg]]) e in Übersicht."""
import calendar
import json
import os
import shutil
import textwrap
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

# I colori stanno solo sui segni; i testi restano in inchiostro neutro (palette validata della skill dataviz).
CSS = """
:root{--bg:#ffffff;--ink:#1d1d1f;--muted:#6e6e73;--line:#e8e8ed;--track:#f2f2f5;
--blue:#2a78d6;--orange:#eb6834;--aqua:#1baf7a;--violet:#6250d6;--yellow:#eda100}
@media (prefers-color-scheme:dark){:root{--bg:#1c1c1e;--ink:#f5f5f7;--muted:#a1a1a6;--line:#2f2f33;--track:#2a2a2d;
--blue:#3987e5;--orange:#d95926;--aqua:#199e70;--violet:#9085e9;--yellow:#c98500}}
text{font-family:-apple-system,"SF Pro Text",system-ui,sans-serif;fill:var(--ink)}
.t{font-size:15px;font-weight:600;letter-spacing:-.2px}.h{font-size:44px;font-weight:600;letter-spacing:-1.2px}
.u{font-size:15px;font-weight:400;letter-spacing:0;fill:var(--muted)}.s{font-size:12px;fill:var(--muted)}.b{font-size:13px}
.pop{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.2,1.4,.4,1) both}
.grow{transform-box:fill-box;transform-origin:bottom;animation:grow .7s cubic-bezier(.2,.8,.2,1) both}
.growx{transform-box:fill-box;transform-origin:left;animation:growx .7s cubic-bezier(.2,.8,.2,1) both}
.draw{stroke-dasharray:1;animation:draw 1.1s ease-out both}.fade{animation:fade .6s ease-out both}
@keyframes pop{from{transform:scale(.3);opacity:0}}@keyframes grow{from{transform:scaleY(0)}}
@keyframes growx{from{transform:scaleX(0)}}@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes fade{from{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""
MONTHS = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
W, H = 340, 300
START = date(2026, 11, 5)  # primo giorno del progetto: prima non esistono "giorni saltati"


def svg(body, w=W, h=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><style>{CSS}</style>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="20" fill="var(--bg)" stroke="var(--line)"/>{body}</svg>')


def real(sessions):
    return [s for s in sessions if not s.get("baseline")]


def streak(days, today):
    """Giorni di fila. Oggi non ancora fatto non spezza la serie: la giornata non è finita."""
    d = today if today in days else today - timedelta(1)
    n = 0
    while d in days:
        n, d = n + 1, d - timedelta(1)
    return n


def week_progress(days, today):
    monday = today - timedelta(today.weekday())
    first = max(monday, min(START, today))
    done = sum(monday + timedelta(i) in days for i in range(7))
    return done, (today - first).days + 1


def calendar_panel(sessions, today):
    kinds = defaultdict(set)
    for s in real(sessions):
        kinds[date.fromisoformat(s["date"])].add(s["kind"])
    days = set(kinds)
    n, (done, elapsed) = streak(days, today), week_progress(days, today)
    out = [f'<text x="24" y="38" class="t">{MONTHS[today.month - 1].capitalize()} {today.year}</text>',
           f'<text x="24" y="86" class="h">{n}<tspan class="u" dx="8">{"giorno" if n == 1 else "giorni"} di fila</tspan></text>',
           f'<text x="316" y="38" class="s" text-anchor="end">{done} su {elapsed} questa settimana</text>']
    step, x0, y0 = 42, 44, 118
    for i, name in enumerate("LMMGVSD"):
        out.append(f'<text x="{x0 + i * step}" y="{y0}" class="s" text-anchor="middle">{name}</text>')
    weeks = calendar.Calendar().monthdatescalendar(today.year, today.month)
    gap = min(26, 170 / len(weeks))
    k = 0
    for r, week in enumerate(weeks):
        for c, d in enumerate(week):
            if d.month != today.month:
                continue
            cx, cy, k = x0 + c * step, y0 + 20 + r * gap, k + 1
            delay = f'style="animation-delay:{k * 18}ms"'
            if d in days:
                col = "--blue" if "call" in kinds[d] else "--orange"
                # la call è un quadrato, l'allenamento un cerchio: la differenza non dipende solo dal colore
                shape = (f'<rect x="{cx - 10}" y="{cy - 10}" width="20" height="20" rx="6"' if "call" in kinds[d]
                         else f'<circle cx="{cx}" cy="{cy}" r="10.5"')
                out.append(f'<g class="pop" {delay}>{shape} fill="var({col})"/>'
                           f'<text x="{cx}" y="{cy + 4}" class="s" text-anchor="middle" style="fill:#fff;font-weight:600">{d.day}</text></g>')
            elif d == today:
                out.append(f'<g class="pop" {delay}><circle cx="{cx}" cy="{cy}" r="10" fill="none" stroke="var(--orange)" stroke-width="2"/>'
                           f'<text x="{cx}" y="{cy + 4}" class="s" text-anchor="middle" style="fill:var(--ink)">{d.day}</text></g>')
            elif START <= d < today:
                out.append(f'<g class="fade" {delay}><circle cx="{cx}" cy="{cy}" r="10" fill="var(--track)"/>'
                           f'<text x="{cx}" y="{cy + 4}" class="s" text-anchor="middle">{d.day}</text></g>')
            else:
                out.append(f'<text x="{cx}" y="{cy + 4}" class="s fade" {delay} text-anchor="middle" opacity=".5">{d.day}</text>')
    return svg("".join(out))


def weeks_of(sessions):
    w = defaultdict(list)
    for s in real(sessions):
        d = date.fromisoformat(s["date"])
        w[d - timedelta(d.weekday())].append(s["voto"])
    return {k: sum(v) / len(v) for k, v in sorted(w.items())}


def vote_panel(sessions, today):
    w = weeks_of(sessions)
    monday = today - timedelta(today.weekday())
    slots = [monday - timedelta(7 * i) for i in range(7, -1, -1)]
    cur, prev = w.get(monday), w.get(monday - timedelta(7))
    head = "–" if cur is None else f"{cur:.1f}".replace(".", ",")
    if cur is not None and prev is not None:
        d = cur - prev
        note = f"{'+' if d >= 0 else '−'}{abs(d):.1f} sulla settimana scorsa".replace(".", ",")
    else:
        note = "media di questa settimana"
    out = ['<text x="24" y="38" class="t">Voto per settimana</text>', f'<text x="24" y="86" class="h">{head}</text>',
           f'<text x="24" y="108" class="s">{note}</text>']
    base, top = 260, 126
    bw = 14
    for i, m in enumerate(slots):
        x = 28 + i * 40
        out.append(f'<rect x="{x}" y="{top}" width="{bw}" height="{base - top}" rx="6" fill="var(--track)"/>')
        if m in w:
            h = max(8, (base - top) * w[m] / 10)
            out.append(f'<rect class="grow" style="animation-delay:{i * 50}ms" x="{x}" y="{base - h}" width="{bw}" height="{h}" rx="6" fill="var(--blue)"/>')
        if i % 2 == 1:
            out.append(f'<text x="{x + bw / 2}" y="{base + 20}" class="s" text-anchor="middle">{m.day}/{m.month}</text>')
    return svg("".join(out))


def line_panel(sessions, key, title, unit, color, note, fmt="{:.0f}"):
    pts = [s for s in sessions if s.get(key) is not None][-14:]
    last = fmt.format(pts[-1][key]).replace(".", ",") if pts else "–"
    out = [f'<text x="24" y="38" class="t">{title}</text>', f'<text x="24" y="86" class="h">{last}<tspan class="u" dx="8">{unit}</tspan></text>', f'<text x="24" y="108" class="s">{note}</text>']
    x0, x1, y0, y1 = 30, 284, 262, 130
    for y in (y0, (y0 + y1) / 2, y1):
        out.append(f'<line x1="{x0 - 4}" x2="{x1 + 4}" y1="{y}" y2="{y}" stroke="var(--line)"/>')
    if pts:
        vals = [p[key] for p in pts]
        lo, hi = min(vals), max(vals)
        pad = max((hi - lo) * .15, 1)
        lo, hi = max(lo - pad, 0), hi + pad
        out += [f'<text x="316" y="{y1 + 4}" class="s" text-anchor="end">{fmt.format(hi).replace(".", ",")}</text>',
                f'<text x="316" y="{y0 + 4}" class="s" text-anchor="end">{fmt.format(lo).replace(".", ",")}</text>']
        step = (x1 - x0) / max(len(pts) - 1, 1)
        xy = [(x0 + i * step, y0 - (v - lo) / (hi - lo) * (y0 - y1)) for i, v in enumerate(vals)]
        if len(xy) > 1:
            d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in xy)
            out.append(f'<path class="draw" pathLength="1" d="{d}" fill="none" stroke="var({color})" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
        for i, ((x, y), p) in enumerate(zip(xy, pts)):
            # punto pieno: simulazione; vuoto: call vera
            fill = "var(--bg)" if p.get("kind") == "call" else f"var({color})"
            out.append(f'<circle class="pop" style="animation-delay:{i * 60}ms" cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{fill}" stroke="var({color})" stroke-width="2"/>')
        out.append('<text x="24" y="284" class="s">● simulazione   ○ call vera</text>')
    return svg("".join(out))


def subscores_panel(sessions):
    labels = [("filo_logico", "Filo logico", "--blue"), ("fluidita", "Fluidità", "--orange"), ("presenza", "Presenza", "--aqua"),
              ("sicurezza", "Sicurezza", "--yellow"), ("conversazione", "Conversazione", "--violet")]
    recent = real(sessions)[-5:] or sessions[-1:]
    out = ['<text x="24" y="38" class="t">Le 5 aree</text>',
           f'<text x="316" y="38" class="s" text-anchor="end">{"ultima sessione" if len(recent) == 1 else f"media delle ultime {len(recent)}"}</text>' if recent else ""]
    for i, (k, name, col) in enumerate(labels):
        y = 72 + i * 44
        v = sum(s["sottovoti"][k] for s in recent) / len(recent) if recent else None
        val = "–" if v is None else f"{v:.1f}".replace(".", ",")
        out += [f'<text x="24" y="{y}" class="b">{name}</text>', f'<text x="316" y="{y}" class="b" text-anchor="end">{val}</text>',
                f'<rect x="24" y="{y + 9}" width="292" height="8" rx="4" fill="var(--track)"/>']
        if v is not None:
            out.append(f'<rect class="growx" style="animation-delay:{i * 70}ms" x="24" y="{y + 9}" width="{292 * v / 10:.1f}" height="8" rx="4" fill="var({col})"/>')
    return svg("".join(out))


def last_panel(sessions):
    if not sessions:
        return svg('<text x="24" y="38" class="t">Ultima sessione</text><text x="24" y="70" class="u">Ancora nessun video.</text>')
    pool = real(sessions) or sessions
    s = pool[-1]
    d = date.fromisoformat(s["date"])
    voto = f"{s['voto']:g}".replace(".", ",")
    out = ['<text x="24" y="38" class="t">Ultima sessione</text>',
           f'<text x="316" y="38" class="s" text-anchor="end">{"Call vera" if s["kind"] == "call" else "Simulazione"} · {d.day} {MONTHS[d.month - 1]}</text>',
           f'<text x="24" y="92" class="h">{voto}<tspan class="u" dx="8">su 10</tspan></text>',
           '<text x="24" y="134" class="s">Prossimo focus</text>']
    for i, line in enumerate(textwrap.wrap(s.get("focus", ""), 40)[:6]):
        out.append(f'<text class="fade" style="animation-delay:{150 + i * 60}ms" x="24" y="{158 + i * 21}" font-size="15">{escape(line)}</text>')
    return svg("".join(out))


PANELS = ("calendario", "voto", "intercalari", "ritmo", "aree", "ultima")
HUB = """---
tipo: area
creato: {day}
---
# Sales Gym

Su: [[Aree]]

Allenamento quotidiano per le sales call. Salva il video in iCloud Drive > Sales Gym; le call vere in Sales Gym > Chiamate.

![[calendario.svg]] ![[ultima.svg]]

![[voto.svg]] ![[aree.svg]]

![[intercalari.svg]] ![[ritmo.svg]]

## Note personali
"""


def render_all(sessions, vault, root, today=None):
    today = today or date.today()
    charts = vault / "Grafici"
    charts.mkdir(parents=True, exist_ok=True)
    out = {
        "calendario": calendar_panel(sessions, today), "voto": vote_panel(sessions, today),
        "intercalari": line_panel(sessions, "fillers_per_min", "Intercalari", "al minuto", "--orange", "Più basso è meglio", "{:.1f}"),
        "ritmo": line_panel(sessions, "wpm", "Ritmo", "parole al minuto", "--aqua", "Quando parli, pause escluse"),
        "aree": subscores_panel(sessions), "ultima": last_panel(sessions),
    }
    for name, text in out.items():
        (charts / f"{name}.svg").write_text(text)
    hub = vault / "Sales Gym.md"
    if not hub.exists():
        hub.write_text(HUB.format(day=today.isoformat()))
    widget = Path(os.environ.get("GYM_WIDGET", Path.home() / "Library/Application Support/Übersicht/widgets/sales-gym.widget"))
    if widget.is_dir():
        for name in PANELS:
            shutil.copy(charts / f"{name}.svg", widget / f"{name}.svg")
        (widget / "version.txt").write_text(json.dumps([len(sessions), today.isoformat()]))
