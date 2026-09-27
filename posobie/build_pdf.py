"""Собирает пособие из src/*.md в свёрстанный PDF (Chromium) и редактируемый DOCX.

Свои блоки в markdown:
  :::box ТИП Заголовок ... :::   — врезка (key, translate, science, practice, warn, red, blue, green)
  :::quadrant ... :::             — карта четырёх типов
  :::lines N ... :::              — N линеек для письма
  ---                             — новая страница
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).parent
TITLE = "Мужская и женская энергия"
OUT = HERE / f"{TITLE} — пособие"
LABELS = {
    "key": "Запомни", "translate": "Перевод", "science": "Наука", "practice": "Практика",
    "warn": "Внимание", "red": "Красный", "blue": "Синий", "green": "Зелёный",
}
BLOCK = re.compile(r"^:::(\w+)[ \t]*([^\n]*)\n(.*?)^:::[ \t]*$", re.S | re.M)

QUADRANT_SVG = """
<svg class="quadrant" viewBox="0 0 520 420" role="img" aria-label="Карта четырёх типов">
  <rect x="70" y="20" width="210" height="170" rx="14" fill="#f3e9f7"/>
  <rect x="290" y="20" width="210" height="170" rx="14" fill="#e6f2ea"/>
  <rect x="70" y="200" width="210" height="170" rx="14" fill="#eeeceb"/>
  <rect x="290" y="200" width="210" height="170" rx="14" fill="#fbeadf"/>
  <g font-family="Manrope, sans-serif" text-anchor="middle">
    <text x="175" y="95" font-size="22" font-weight="800" fill="#6b3f7d">Удобная</text>
    <text x="175" y="122" font-size="13" fill="#5b5057">Быть ↑ · Делать ↓</text>
    <text x="395" y="95" font-size="22" font-weight="800" fill="#2f6b45">Живая</text>
    <text x="395" y="122" font-size="13" fill="#5b5057">обе способности развиты</text>
    <text x="175" y="275" font-size="22" font-weight="800" fill="#5b5057">Выжатая</text>
    <text x="175" y="302" font-size="13" fill="#5b5057">обе проседают</text>
    <text x="395" y="275" font-size="22" font-weight="800" fill="#a4512a">Ломовая лошадь</text>
    <text x="395" y="302" font-size="13" fill="#5b5057">Делать ↑ · Быть ↓</text>
    <text x="285" y="405" font-size="14" font-weight="700" fill="#8a3b5c">энергия «Делать» →</text>
    <text x="24" y="195" font-size="14" font-weight="700" fill="#8a3b5c" transform="rotate(-90 24 195)">энергия «Быть» →</text>
  </g>
</svg>"""

CSS = """
@import url('fonts/fonts.css');
@page { size: A4; margin: 20mm 19mm 20mm 19mm;
  @bottom-center { content: counter(page); font-family: Manrope, sans-serif; font-size: 8.5pt; color: #9a8a92; } }
@page :first { margin: 0; @bottom-center { content: none; } }
:root { --ink:#231c20; --muted:#6d6168; --accent:#8a3b5c; --accent-2:#c9728f; --soft:#f8eff3; --line:#ead9e1; }
* { box-sizing: border-box; }
html, body { background:#fff; }
body { font-family: 'Lora', Georgia, serif; color: var(--ink); font-size: 10.8pt; line-height: 1.58; margin:0; }
h1, h2, h3, h4, .box-title, th, .chip { font-family: 'Manrope', 'DejaVu Sans', sans-serif; }

.cover { height: 297mm; width: 210mm; padding: 28mm 22mm; display:flex; flex-direction:column; justify-content:space-between;
  background: radial-gradient(circle at 85% 18%, #f6dde7 0, transparent 38%), radial-gradient(circle at 10% 90%, #efe4f6 0, transparent 40%), #fffaf8; }
.cover .kicker { letter-spacing:.22em; text-transform:uppercase; color:var(--accent); font: 800 9.5pt Manrope, sans-serif; }
.cover h1 { font-size: 44pt; line-height:1.04; margin: 8mm 0 7mm; font-weight:800; letter-spacing:-.01em; }
.cover h1 span { color: var(--accent); display:block; }
.cover .lead { font-size: 15pt; color: var(--muted); max-width: 135mm; line-height:1.45; }
.cover .rings { display:flex; align-items:center; gap:0; margin-top: 16mm; }
.cover .ring { width: 58mm; height: 58mm; border-radius: 50%; display:flex; align-items:center; justify-content:center;
  font: 800 15pt Manrope, sans-serif; mix-blend-mode: multiply; }
.cover .ring.a { background: #f2c9d6; color:#6e2743; }
.cover .ring.b { background: #d9c9ef; color:#4b2d73; margin-left: -16mm; }
.cover .foot { font: 600 10pt Manrope, sans-serif; color: var(--muted); display:flex; justify-content:space-between; border-top:1px solid var(--line); padding-top:5mm; }

.toc { page-break-after: always; }
.toc h2 { margin-bottom: 8mm; }
.toc ol { list-style: none; padding: 0; margin: 0; counter-reset: none; }
.toc li { font: 600 12pt Manrope, sans-serif; padding: 3.2mm 0; border-bottom: 1px solid var(--line); display:flex; gap: 5mm; }
.toc li span.n { color: var(--accent); min-width: 16mm; }

section { page-break-before: always; }
h2 { font-size: 24pt; color: var(--ink); margin: 0 0 7mm; font-weight:800; line-height:1.12; letter-spacing:-.01em; }
h2 .chip { display:block; font-size: 9pt; letter-spacing:.2em; text-transform:uppercase; color: var(--accent); margin-bottom: 3mm; }
h3 { font-size: 14pt; margin: 8mm 0 3mm; color: var(--accent); font-weight:800; page-break-after: avoid; }
p { margin: 0 0 3.2mm; orphans:3; widows:3; }
ul, ol { margin: 0 0 4mm; padding-left: 5.5mm; } li { margin-bottom: 1.5mm; }
li::marker { color: var(--accent); }
strong { font-weight: 600; }
a { color: var(--accent); word-break: break-all; text-decoration: none; }

.box { margin: 5mm 0; padding: 5mm 6mm 3.5mm; border-radius: 10px; background: var(--soft); page-break-inside: avoid; border: 1px solid transparent; }
.box .box-title { font-size: 11.5pt; font-weight: 800; margin-bottom: 2.5mm; display:flex; align-items:center; gap: 3mm; }
.box .chip { font-size: 7.5pt; letter-spacing: .14em; text-transform: uppercase; padding: 1mm 2.4mm; border-radius: 99px; background: var(--accent); color:#fff; font-weight:800; }
.box ul { padding-left: 5mm; }
.box.key { background: #fbeef3; border-color: #f0cfdc; }
.box.translate { background: #f4f0fb; border-color: #e0d5f2; } .box.translate .chip { background:#6b4a9e; }
.box.science { background: #eef5f8; border-color: #d3e5ee; } .box.science .chip { background:#2f6f8f; }
.box.practice { background: #f1f7f1; border-color: #d6e9d8; } .box.practice .chip { background:#3d7a4f; }
.box.warn { background: #fff5e8; border-color: #f3dcb9; } .box.warn .chip { background:#b36b12; }
.box.red { background: #fdeceb; border-color:#f4c9c5; } .box.red .chip { background:#c0392b; }
.box.blue { background: #ecf1fb; border-color:#cad7f1; } .box.blue .chip { background:#3860b0; }
.box.green { background: #edf7ee; border-color:#cde8d0; } .box.green .chip { background:#2e8b4a; }
.box.warn ul, .box ul.checks { list-style: none; padding-left: 0; }

table { width:100%; border-collapse: collapse; margin: 3mm 0 6mm; font-size: 9.6pt; line-height: 1.4; }
th { text-align:left; background: var(--accent); color:#fff; padding: 2.2mm 2.6mm; font-weight:700; }
td { padding: 2.2mm 2.6mm; border-bottom: 1px solid var(--line); vertical-align: top; }
tr { page-break-inside: avoid; }
tbody tr:nth-child(even) td { background: #fdf8fa; }
td:empty::after { content: "\\00a0"; }
table.sheet td { height: 11mm; }
table.test td:nth-child(n+3), table.test th:nth-child(n+3) { text-align:center; width: 8mm; color:#b9a3ae; }
table.test td:first-child { color: var(--muted); width: 8mm; }
.quadrant { width: 100%; max-width: 118mm; display:block; margin: 4mm auto 6mm; }
.lines div { border-bottom: 1px solid #cbb8c2; height: 9mm; }
.sources li { font-size: 8.6pt; color: var(--muted); line-height: 1.45; }
.blank { display:inline-block; border-bottom: 1px solid #b9a3ae; height: 1.1em; vertical-align: -2px; margin: 0 1.5mm; }
.fine { font-size: 8.6pt; color: var(--muted); }
"""


def blocks_to_html(md, holders):
    def repl(m):
        kind, arg, body = m.group(1), m.group(2).strip(), m.group(3)
        if kind == "box":
            typ, _, title = arg.partition(" ")
            inner = markdown.markdown(fix_md(body), extensions=["tables"])
            inner = inner.replace("<ul>", '<ul class="checks">') if "☐" in body else inner
            html = (f'<div class="box {typ}"><div class="box-title"><span class="chip">{LABELS.get(typ, typ)}</span>'
                    f"{title}</div>{inner}</div>")
        elif kind == "quadrant":
            html = QUADRANT_SVG
        elif kind == "lines":
            html = '<div class="lines">' + "<div></div>" * int(arg or 4) + "</div>"
        else:
            raise ValueError(kind)
        holders.append(html)
        return f"\n\nHOLDER{len(holders) - 1}X\n\n"
    return BLOCK.sub(repl, md)


def fix_md(text):
    """Пустая строка перед списками (иначе markdown их не видит) и линейки вместо подчёркиваний."""
    out, prev = [], ""
    for line in text.split("\n"):
        is_item = re.match(r"^(- |\d+\. )", line)
        if is_item and prev.strip() and not re.match(r"^(- |\d+\. )", prev):
            out.append("")
        out.append(line)
        prev = line
    text = "\n".join(out)
    return re.sub(r"_{4,}", lambda m: f'<span class="blank" style="width:{min(len(m.group(0)) * 2.2, 90):.0f}mm"></span>', text)


def section_html(chunk):
    holders = []
    chunk = fix_md(chunk)
    md = blocks_to_html(chunk, holders)
    html = markdown.markdown(md, extensions=["tables"])
    for i, h in enumerate(holders):
        html = html.replace(f"<p>HOLDER{i}X</p>", h)
    # таблица теста и рабочие листы с пустыми клетками
    html = re.sub(r"<table>(\s*<thead>\s*<tr>\s*<th>№</th>)", r'<table class="test">\1', html)
    html = re.sub(r"<table>((?:(?!</table>).)*?<td></td>)", r'<table class="sheet">\1', html, flags=re.S)
    m = re.match(r"\s*<h2>(Глава \d+)\. (.+?)</h2>", html)
    if m:
        html = html.replace(m.group(0), f'<h2><span class="chip">{m.group(1)}</span>{m.group(2)}</h2>', 1)
    cls = ' class="sources"' if chunk.lstrip().startswith("## Источники") else ""
    return f"<section{cls}>{html}</section>"


def main():
    md = "\n\n---\n\n".join(p.read_text(encoding="utf-8").strip() for p in sorted((HERE / "src").glob("*.md")))
    chunks = [c.strip() for c in re.split(r"^---\s*$", md, flags=re.M) if c.strip()]
    heads = [re.match(r"## (.+)", c).group(1) for c in chunks if c.startswith("## ") and not c.startswith("## Лист")]
    toc = ""
    for h in heads:
        m = re.match(r"Глава (\d+)\. (.+)", h)
        num, name = (m.group(1), m.group(2)) if m else ("—", h)
        toc += f'<li><span class="n">{num}</span>{name}</li>'
    cover = f"""<div class="cover"><div>
      <div class="kicker">Пособие · перевод на человеческий язык</div>
      <h1>Мужская и женская энергия<span>что это на самом деле</span></h1>
      <p class="lead">Понятное объяснение без эзотерики, тест «Карта энергий», 16 практик, программа на 21 день и рабочие листы</p>
      <div class="rings"><div class="ring a">Делать</div><div class="ring b">Быть</div></div></div>
      <div class="foot"><span>Наука · Практика · Отношения</span><span>2026</span></div></div>"""
    body = cover + f'<div class="toc"><h2>Содержание</h2><ol>{toc}</ol></div>' + "".join(section_html(c) for c in chunks)
    html_path = HERE / "posobie.html"
    html_path.write_text(
        f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{TITLE}</title><style>{CSS}</style></head><body>{body}</body></html>", encoding="utf-8")

    js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://{html_path}', {{ waitUntil: 'networkidle' }});
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({{ path: {str(OUT) + '.pdf'!r}, printBackground: true, preferCSSPageSize: true }});
  await b.close();
}})();"""
    env = {**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()}
    subprocess.run(["node", "-e", js], check=True, env=env)

    # DOCX: те же тексты, врезки превращаются в цитаты-плашки
    def to_plain(m):
        kind, arg, body = m.group(1), m.group(2).strip(), m.group(3)
        if kind == "box":
            typ, _, title = arg.partition(" ")
            lines = [f"**{LABELS.get(typ, typ).upper()}. {title}**", ""] + body.strip().splitlines()
            return "\n".join("> " + l if l.strip() else ">" for l in lines) + "\n"
        if kind == "quadrant":
            return ("| | «Делать» слабое | «Делать» сильное |\n|---|---|---|\n"
                    "| **«Быть» сильное** | Удобная | Живая |\n| **«Быть» слабое** | Выжатая | Ломовая лошадь |\n")
        if kind == "lines":
            return "\n".join(["_" * 70] * int(arg or 4)) + "\n"
    plain = f"# {TITLE}: что это на самом деле\n\n" + BLOCK.sub(to_plain, md)
    tmp = HERE / "posobie_docx.md"
    tmp.write_text(plain, encoding="utf-8")
    sys.path.insert(0, str(HERE.parent / "research"))
    subprocess.run([sys.executable, str(HERE.parent / "research" / "md2docx.py"), str(tmp), str(OUT) + ".docx"], check=True)
    tmp.unlink()
    print("ok")


main()
