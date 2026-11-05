"""Build one self-contained HTML page from a RePoG session review.

    python build_page.py --work DIR --runtime DIR --check FILE --report FILE --out FILE
                         [--title TEXT] [--play-start N]

--work     folder holding turns.jsonl and quant.json from extract.py
--runtime  the campaign's .repog-runtime folder (lint_history.jsonl, rolls.jsonl)
--check    check_state --scope full output (JSON)
--report   the review report in Markdown (optional; the page says so if missing)

The page has no external dependencies: charts are inline SVG and the report is
converted by the small Markdown renderer below. Nothing here reads or writes
the live campaign.
"""

from __future__ import annotations

import argparse
import collections
import html
import json
import re
import statistics
from pathlib import Path

RULE_LABELS = {
    "repetition": "Tekrar",
    "pc_authoring": "Oyuncu karakterini yazma",
    "restatement": "Oyuncunun sözünü tekrar",
    "avoid_phrase": "Yasaklı kalıp",
    "meta_leak": "Sistem dili sızıntısı",
    "negated_description": "Olumsuz betimleme zinciri",
    "out_of_language": "Dil dışı satır",
    "calque": "Çeviri kalıbı",
    "tracker_leak": "Takip sayısı sızıntısı",
    "stock_beat": "Klişe vuruş",
}
BAND_LABELS = [
    ("critical_success", "Kritik"),
    ("clean_success", "Temiz"),
    ("success_with_cost", "Bedelli"),
    ("partial_or_loss", "Kısmi"),
    ("failure", "Başarısız"),
]


# --------------------------------------------------------------------------- data


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def median(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "–"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


# ----------------------------------------------------------------------- markdown


INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def inline(text: str) -> str:
    codes: list[str] = []

    def keep(match: re.Match) -> str:
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = INLINE_CODE_RE.sub(keep, text)
    text = esc(text)
    text = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}" rel="noopener" target="_blank">{m.group(1)}</a>', text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{esc(codes[int(m.group(1))])}</code>", text)


def markdown_to_html(source: str) -> str:
    lines = source.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    list_stack: list[tuple[str, int]] = []  # (tag, indent)
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def close_lists(to_indent: int = -1) -> None:
        while list_stack and list_stack[-1][1] > to_indent:
            out.append(f"</li></{list_stack.pop()[0]}>")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            close_lists()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            out.append("<pre><code>" + esc("\n".join(block)) + "</code></pre>")
            i += 1
            continue
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            close_lists()
            level = min(len(heading.group(1)) + 1, 5)
            text = heading.group(2)
            anchor = re.sub(r"[^\w]+", "-", text.lower()).strip("-")[:60]
            out.append(f'<h{level} id="r-{esc(anchor)}">{inline(text)}</h{level}>')
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]) and "-" in lines[i + 1]:
            flush_paragraph()
            close_lists()
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            table = ['<div class="table-wrap"><table><thead><tr>']
            table += [f"<th>{inline(c)}</th>" for c in header]
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            table.append("</tbody></table></div>")
            out.append("".join(table))
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            close_lists()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            continue
        item = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)$", line)
        if item:
            flush_paragraph()
            indent = len(item.group(1).replace("\t", "    "))
            tag = "ol" if item.group(2)[0].isdigit() else "ul"
            if not list_stack or indent > list_stack[-1][1]:
                out.append(f"<{tag}><li>")
                list_stack.append((tag, indent))
            else:
                close_lists(indent)
                if list_stack and list_stack[-1][1] == indent:
                    out.append("</li><li>")
                else:
                    out.append(f"<{tag}><li>")
                    list_stack.append((tag, indent))
            out.append(inline(item.group(3)))
            i += 1
            continue
        if list_stack and line.startswith(" "):
            out.append(" " + inline(stripped))
            i += 1
            continue
        close_lists()
        paragraph.append(stripped)
        i += 1
    flush_paragraph()
    close_lists()
    return "\n".join(out)


# ------------------------------------------------------------------------- charts


def timeline_svg(turns: list[dict], play_start: int, distill_turns: set[int]) -> str:
    width, height, pad_l, pad_b, pad_t = 1000, 260, 44, 28, 14
    cap = 300.0
    n = len(turns)
    if not n:
        return ""
    bar_w = (width - pad_l - 6) / n
    plot_h = height - pad_b - pad_t
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Tur başına bekleme süresi" class="chart">']
    for tick in (60, 120, 180, 240, 300):
        y = pad_t + plot_h * (1 - tick / cap)
        parts.append(f'<line x1="{pad_l}" x2="{width}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" class="axis" text-anchor="end">{tick}s</text>')
    for k, turn in enumerate(turns):
        wait = turn.get("wait_s") or 0
        h = plot_h * min(wait, cap) / cap
        x = pad_l + k * bar_w
        idx = turn["idx"]
        cls = "bar-s0" if idx < play_start else ("bar-distill" if idx in distill_turns else "bar-play")
        title = f"T{idx}: {wait:.0f} s" + (" · OOC" if turn.get("ooc") else "") + (" · distill" if idx in distill_turns else "")
        parts.append(
            f'<rect x="{x:.2f}" y="{pad_t + plot_h - h:.1f}" width="{max(bar_w - 0.6, 0.6):.2f}" height="{h:.1f}" class="{cls}"><title>{esc(title)}</title></rect>'
        )
        if wait > cap:
            parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{pad_t + 9}" class="clip" text-anchor="middle">▲</text>')
        if turn.get("ooc"):
            parts.append(f'<circle cx="{x + bar_w / 2:.1f}" cy="{pad_t + plot_h + 8}" r="2.6" class="ooc"><title>T{idx} OOC</title></circle>')
        if turn.get("compaction_before"):
            parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{pad_t}" y2="{pad_t + plot_h}" class="compact"/>')
            parts.append(f'<text x="{x + 3:.1f}" y="{pad_t + 10}" class="axis">sıkıştırma</text>')
        if idx % 25 == 0:
            parts.append(f'<text x="{x:.1f}" y="{height - 4}" class="axis" text-anchor="middle">T{idx}</text>')
    play_x = pad_l + (play_start - turns[0]["idx"]) * bar_w
    parts.append(f'<line x1="{play_x:.1f}" x2="{play_x:.1f}" y1="{pad_t}" y2="{pad_t + plot_h}" class="phase"/>')
    parts.append(f'<text x="{play_x + 4:.1f}" y="{pad_t + 24}" class="axis strong">oyun başlıyor</text>')
    parts.append("</svg>")
    return "".join(parts)


def lint_heatmap(rows: list[dict], window: int = 20) -> str:
    if not rows:
        return "<p class='muted'>Denetim geçmişi yok.</p>"
    windows = [rows[i : i + window] for i in range(0, len(rows), window)]
    rules = collections.Counter()
    for row in rows:
        rules.update({k: 1 for k, v in (row.get("counts") or {}).items() if v})
    ordered = [rule for rule, _ in rules.most_common()]
    if not ordered:
        return "<p class='muted'>Hiç bulgu yok.</p>"
    head = "".join(
        f"<th>{i * window + 1}–{i * window + len(w)}</th>" for i, w in enumerate(windows)
    )
    body = []
    for rule in ordered:
        cells = []
        for w in windows:
            hit = sum(1 for r in w if (r.get("counts") or {}).get(rule))
            share = hit / len(w)
            alpha = min(0.08 + share * 1.6, 0.95) if hit else 0
            style = f"background: rgba(var(--heat), {alpha:.2f})" if hit else ""
            cells.append(f'<td style="{style}" title="{hit}/{len(w)}">{share:.0%}</td>' if hit else '<td class="zero">·</td>')
        total = rules[rule]
        body.append(
            f"<tr><th scope='row'>{esc(RULE_LABELS.get(rule, rule))}<span class='muted'> {total}/{len(rows)}</span></th>{''.join(cells)}</tr>"
        )
    return (
        "<div class='table-wrap'><table class='heat'><thead><tr><th>Kural · denetlenen yanıt</th>"
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def bands_svg(rolls: list[dict]) -> str:
    counts = collections.Counter(r.get("band") for r in rolls)
    total = sum(counts.values()) or 1
    width, bar_h, gap = 520, 22, 8
    parts = [f'<svg viewBox="0 0 {width} {len(BAND_LABELS) * (bar_h + gap)}" class="chart small" role="img" aria-label="Zar sonuçları">']
    for k, (band, label) in enumerate(BAND_LABELS):
        value = counts.get(band, 0)
        w = (width - 170) * value / total
        y = k * (bar_h + gap)
        parts.append(f'<text x="0" y="{y + 16}" class="axis">{esc(label)}</text>')
        parts.append(f'<rect x="90" y="{y}" width="{max(w, 1):.1f}" height="{bar_h}" class="band band-{k}"><title>{value}</title></rect>')
        parts.append(f'<text x="{96 + w:.1f}" y="{y + 16}" class="axis">{value} ({value / total:.0%})</text>')
    parts.append("</svg>")
    return "".join(parts)


def margin_svg(rolls: list[dict]) -> str:
    margins = [int(r["margin"]) for r in rolls if isinstance(r.get("margin"), int)]
    if not margins:
        return ""
    lo, hi = min(min(margins), -6), max(max(margins), 10)
    counts = collections.Counter(margins)
    width, height, pad_b = 520, 150, 22
    step = width / (hi - lo + 1)
    peak = max(counts.values())
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart small" role="img" aria-label="Zar farkı dağılımı">']
    for m in range(lo, hi + 1):
        x = (m - lo) * step
        h = (height - pad_b - 6) * counts.get(m, 0) / peak
        cls = "m-fail" if m <= -4 else "m-partial" if m < 0 else "m-cost" if m == 0 else "m-win"
        if counts.get(m):
            parts.append(f'<rect x="{x + 1:.1f}" y="{height - pad_b - h:.1f}" width="{step - 2:.1f}" height="{h:.1f}" class="{cls}"><title>fark {m}: {counts[m]}</title></rect>')
        if m % 2 == 0:
            parts.append(f'<text x="{x + step / 2:.1f}" y="{height - 6}" class="axis" text-anchor="middle">{m:+d}</text>')
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- page


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a65;--card:#ffffff;--line:#e4e1d8;--accent:#2f5d8a;
--s0:#b9b6ab;--play:#3d6f9e;--distill:#d08a2c;--ooc:#c0392b;--compact:#7a4fa3;--heat:192,57,43;
--b0:#2e7d4f;--b1:#4f9d69;--b2:#c9a227;--b3:#d0742c;--b4:#b03a2e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#ecebe6;--muted:#a3a19a;--card:#1f1f1d;--line:#34332f;--accent:#8fb6dc;
--s0:#5d5b55;--play:#6e9fcc;--distill:#e0a24d;--ooc:#e2645a;--compact:#b48ad8;--heat:226,100,90}}
:root[data-theme="dark"]{--bg:#161615;--fg:#ecebe6;--muted:#a3a19a;--card:#1f1f1d;--line:#34332f;--accent:#8fb6dc;
--s0:#5d5b55;--play:#6e9fcc;--distill:#e0a24d;--ooc:#e2645a;--compact:#b48ad8;--heat:226,100,90}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.25rem;margin:40px 0 12px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:1.08rem;margin:28px 0 8px}h4,h5{font-size:1rem;margin:20px 0 6px}
.muted{color:var(--muted)}nav{display:flex;flex-wrap:wrap;gap:6px 14px;margin:14px 0 6px;font-size:.92rem}
nav a{color:var(--accent);text-decoration:none}nav a:hover{text-decoration:underline}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:18px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.tile b{display:block;font-size:1.35rem}.tile span{color:var(--muted);font-size:.85rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.chart{width:100%;height:auto;display:block}.chart.small{max-width:560px}
.chart text{font-size:11px;fill:var(--muted)}.chart .strong{fill:var(--fg);font-weight:600}
.grid{stroke:var(--line);stroke-width:1}.bar-s0{fill:var(--s0)}.bar-play{fill:var(--play)}.bar-distill{fill:var(--distill)}
.ooc{fill:var(--ooc)}.compact{stroke:var(--compact);stroke-dasharray:4 3;stroke-width:1.4}.phase{stroke:var(--fg);stroke-width:1.2}
.clip{fill:var(--ooc)!important}.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.85rem;color:var(--muted);margin-top:6px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.band-0{fill:var(--b0)}.band-1{fill:var(--b1)}.band-2{fill:var(--b2)}.band-3{fill:var(--b3)}.band-4{fill:var(--b4)}
.m-win{fill:var(--b1)}.m-cost{fill:var(--b2)}.m-partial{fill:var(--b3)}.m-fail{fill:var(--b4)}
.table-wrap{overflow-x:auto;margin:10px 0}table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
thead th{font-weight:600;color:var(--muted);white-space:nowrap}
table.heat td{text-align:center;min-width:46px}table.heat td.zero{color:var(--line)}
code{font:0.88em ui-monospace,SFMono-Regular,Consolas,monospace;background:rgba(127,127,127,.12);padding:1px 4px;border-radius:4px}
pre{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;overflow-x:auto}
pre code{background:none;padding:0}blockquote{margin:10px 0;padding:6px 14px;border-left:3px solid var(--accent);color:var(--muted)}
.report a{color:var(--accent)}.report ul,.report ol{padding-left:22px}
.theme{float:right;font-size:.85rem;background:none;border:1px solid var(--line);border-radius:6px;color:var(--fg);padding:3px 8px;cursor:pointer}
@media (max-width:600px){h1{font-size:1.3rem}.tile b{font-size:1.15rem}}
"""


def build(args: argparse.Namespace) -> str:
    work = Path(args.work)
    turns = read_jsonl(work / "turns.jsonl")
    quant = json.loads((work / "quant.json").read_text(encoding="utf-8")) if (work / "quant.json").is_file() else {}
    runtime = Path(args.runtime) if args.runtime else None
    lint = read_jsonl(runtime / "lint_history.jsonl") if runtime else []
    # Reread rows (0.4.0) amend an earlier receipt; they are not rolls.
    rolls = [r for r in read_jsonl(runtime / "rolls.jsonl") if r.get("kind") != "reread"] if runtime else []
    check = json.loads(Path(args.check).read_text(encoding="utf-8")) if args.check and Path(args.check).is_file() else {}
    report = Path(args.report).read_text(encoding="utf-8") if args.report and Path(args.report).is_file() else ""

    play_start = args.play_start or next(
        (t["idx"] for t in turns if any("commit-durable" in h for h in t.get("helpers", []))), 1
    )
    play = [t for t in turns if t["idx"] >= play_start]
    distill_turns = {t["idx"] for t in turns if any("commit-distill" in h for h in t.get("helpers", []))}
    waits = [float(t["wait_s"]) for t in play if t.get("wait_s") is not None]
    p90 = sorted(waits)[int(len(waits) * 0.9)] if waits else None
    wins = sum(1 for r in rolls if r.get("band") in ("critical_success", "clean_success", "success_with_cost"))
    ooc_play = sum(1 for t in play if t.get("ooc"))
    efforts = collections.Counter(k for t in turns for k in (t.get("efforts") or {}))
    span = f"{(turns[0]['prompt_ts'] or '')[:10]} – {(turns[-1]['last_ts'] or '')[:10]}" if turns else ""

    tiles = [
        (len(turns), "toplam tur"),
        (len(play), f"oyun turu (T{play_start}'den)"),
        (f"{median(waits):.0f} s" if waits else "–", "oyunda medyan bekleme"),
        (f"{p90:.0f} s" if p90 else "–", "oyunda p90 bekleme"),
        (f"{ooc_play} ({pct(ooc_play, len(play))})", "OOC içeren oyun turu"),
        (f"{wins}/{len(rolls)}", "başarılı zar"),
        (len(distill_turns), "distill turu"),
        (len(quant.get("compactions", [])), "sıkıştırma"),
        (f"{median([float(t.get('reply_words') or 0) for t in play]) or 0:.0f}", "medyan yanıt (kelime)"),
    ]
    tiles_html = "".join(f"<div class='tile'><b>{esc(v)}</b><span>{esc(k)}</span></div>" for v, k in tiles)

    helpers = collections.Counter()
    for t in turns:
        helpers.update(t.get("helper_counts") or {})
    helper_rows = "".join(f"<tr><td><code>{esc(k)}</code></td><td>{v}</td></tr>" for k, v in helpers.most_common(24))

    findings = check.get("findings") or []
    finding_rows = "".join(
        f"<tr><td>{esc(f.get('severity'))}</td><td><code>{esc(f.get('rule'))}</code></td><td>{esc(f.get('message', ''))[:400]}</td></tr>"
        for f in findings
    )
    order = quant.get("order", {})
    values = [r["call"]["value"] - r["call"]["difficulty"] for r in rolls if isinstance(r.get("call"), dict) and "value" in r["call"]]

    sections = [
        ("zaman", "Tur zaman çizelgesi", f"""
<p class="muted">Her çubuk bir tur: oyuncunun mesajından modelin son yanıtına kadar geçen süre (300 s'de kesilir, ▲ daha uzun).
Kırmızı nokta OOC içeren tur, kesikli mor çizgi sıkıştırma.</p>
<div class="card">{timeline_svg(turns, play_start, distill_turns)}
<div class="legend"><span><i style="background:var(--s0)"></i>Session 0</span><span><i style="background:var(--play)"></i>oyun</span>
<span><i style="background:var(--distill)"></i>distill turu</span><span><i style="background:var(--ooc)"></i>OOC</span>
<span><i style="background:var(--compact)"></i>sıkıştırma</span></div></div>
<p>Kayıt sırası (oyun turlarında): önce kayıt <b>{order.get('commit_first', 0)}</b>, önce anlatı <b>{order.get('narrate_first', 0)}</b>, kayıtsız <b>{order.get('no_commit', 0)}</b> (Session 0 dahil).
Uygulamanın "bir süredir haber vermedin" uyarısı: <b>{quant.get('silent_reminders', 0)}</b> boş yanıt, ayrıca ilerleme hatırlatmaları.</p>
"""),
        ("lint", "Sunum denetimi", f"""
<p class="muted">Her sütun 20 denetlenmiş yanıt; hücre, o kuralın en az bir kez çıktığı yanıtların oranı. Kaynak: <code>.repog-runtime/lint_history.jsonl</code> ({len(lint)} yanıt).</p>
<div class="card">{lint_heatmap(lint)}</div>
"""),
        ("zar", "Zarlar", f"""
<div class="card"><p><b>{len(rolls)}</b> makbuzlu atış, <b>{sum(1 for r in rolls if r.get('consumed_revision') is not None)}</b> tanesi bir kayda bağlanmış.
Değer − zorluk medyanı <b>{median(values) if values else '–'}</b>.</p>
{bands_svg(rolls)}
<p class="muted" style="margin-top:14px">Sonuç farkı dağılımı (2d6 + değer + etkenler − zorluk; ≤−4 başarısız, −1..−3 kısmi, 0 bedelli, ≥+1 başarı):</p>
{margin_svg(rolls)}</div>
"""),
        ("arac", "Yardımcı araç kullanımı", f"<div class='card table-wrap'><table><thead><tr><th>Yardımcı</th><th>Çağrı</th></tr></thead><tbody>{helper_rows}</tbody></table></div>"),
        ("denetim", "Tam denetim (kampanya kopyası)", f"""
<p>{esc(check.get('error_count', '–'))} hata, {esc(check.get('warning_count', '–'))} uyarı.</p>
<div class="card table-wrap"><table><thead><tr><th>Düzey</th><th>Kural</th><th>Mesaj</th></tr></thead><tbody>{finding_rows}</tbody></table></div>
"""),
    ]
    report_html = markdown_to_html(report) if report else "<p class='muted'>Rapor henüz yok.</p>"
    nav = "".join(f"<a href='#{k}'>{esc(t)}</a>" for k, t in [("rapor", "Rapor")] + [(k, t) for k, t, _ in sections])
    body = "".join(f"<section id='{k}'><h2>{esc(t)}</h2>{content}</section>" for k, t, content in sections)
    title = args.title or "RePoG oturum incelemesi"
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head>
<body><main>
<button class="theme" onclick="var r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'">Tema</button>
<h1>{esc(title)}</h1>
<p class="muted">{esc(span)} · model eforu: {esc(', '.join(efforts) or '–')} · {len(turns)} tur</p>
<nav>{nav}</nav>
<div class="tiles">{tiles_html}</div>
<section id="rapor" class="report"><h2>Rapor</h2>{report_html}</section>
{body}
</main></body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True)
    parser.add_argument("--runtime")
    parser.add_argument("--check")
    parser.add_argument("--report")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title")
    parser.add_argument("--play-start", type=int)
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build(args).encode("utf-8"))
    print(out)


if __name__ == "__main__":
    main()
