"""Собирает posobie.md в свёрстанный HTML и PDF (через Chromium/Playwright)."""
import re
import subprocess
from pathlib import Path

import markdown

HERE = Path(__file__).parent
SRC = HERE / "posobie.md"
HTML = HERE / "posobie.html"
PDF = HERE / "Мужская и женская энергия — пособие.pdf"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Manrope:wght@500;700;800&display=swap');
@page { size: A4; margin: 22mm 20mm 20mm 20mm; }
:root { --ink:#221c1f; --muted:#6d6168; --accent:#8a3b5c; --soft:#f7eef2; --line:#e6d6de; }
html { background:#fff; }
body { font-family: 'Lora', Georgia, 'DejaVu Serif', serif; color: var(--ink); font-size: 11pt; line-height: 1.55; margin:0; }
h1, h2, h3 { font-family: 'Manrope', 'DejaVu Sans', sans-serif; line-height: 1.2; }
.cover { height: 250mm; display:flex; flex-direction:column; justify-content:center; page-break-after: always; }
.cover .kicker { font-family:'Manrope',sans-serif; letter-spacing:.18em; text-transform:uppercase; color:var(--accent); font-weight:700; font-size:10pt; }
.cover h1 { font-size: 38pt; margin: 10mm 0 8mm; color: var(--ink); font-weight:800; }
.cover h1 span { color: var(--accent); }
.cover p { font-size: 14pt; color: var(--muted); max-width: 130mm; }
.cover .bar { width: 40mm; height: 4px; background: var(--accent); margin-top: 12mm; }
section { page-break-before: always; }
section:first-of-type { page-break-before: auto; }
h2 { font-size: 21pt; color: var(--accent); margin: 0 0 6mm; font-weight:800; }
h3 { font-size: 13pt; margin: 7mm 0 2mm; color: var(--ink); font-weight:700; page-break-after: avoid; }
p { margin: 0 0 3.2mm; orphans:3; widows:3; }
ul { margin: 0 0 4mm; padding-left: 6mm; } li { margin-bottom: 1.6mm; }
strong { font-weight: 600; }
blockquote { margin: 5mm 0; padding: 5mm 6mm; background: var(--soft); border-left: 4px solid var(--accent); border-radius: 0 6px 6px 0; page-break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
table { width:100%; border-collapse: collapse; margin: 4mm 0 6mm; font-size: 10pt; }
th { font-family:'Manrope',sans-serif; text-align:left; background: var(--accent); color:#fff; padding: 2.5mm 3mm; }
td { padding: 2.5mm 3mm; border-bottom: 1px solid var(--line); vertical-align: top; }
tr { page-break-inside: avoid; }
td:first-child { font-weight:600; width: 38%; }
a { color: var(--accent); word-break: break-all; }
.sources li { font-size: 9pt; color: var(--muted); }
"""


def main():
    md = SRC.read_text(encoding="utf-8")
    title_block, *chunks = [c.strip() for c in re.split(r"^---\s*$", md, flags=re.M)]
    subtitle = title_block.splitlines()[-1].strip()
    cover = (
        '<div class="cover"><div class="kicker">Пособие</div>'
        '<h1>Мужская и женская энергия: <span>перевод на человеческий язык</span></h1>'
        f'<p>{subtitle}</p><div class="bar"></div></div>'
    )
    sections = []
    for c in chunks:
        html = markdown.markdown(c, extensions=["tables"])
        cls = ' class="sources"' if c.startswith("## Источники") else ""
        sections.append(f"<section{cls}>{html}</section>")
    HTML.write_text(
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>Мужская и женская энергия</title><style>{CSS}</style></head><body>"
        + cover + "".join(sections) + "</body></html>",
        encoding="utf-8",
    )
    js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://{HTML}', {{ waitUntil: 'networkidle' }});
  await p.pdf({{ path: {str(PDF)!r}, format: 'A4', printBackground: true, preferCSSPageSize: true }});
  await b.close();
}})();
"""
    subprocess.run(["node", "-e", js], check=True, env={**__import__("os").environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()})
    print("ok", PDF)


main()
