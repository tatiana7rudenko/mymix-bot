"""Build the workbook: content/*.txt (mini-DSL) -> workbook.html -> PDF via headless Chromium."""
import re, glob, html, subprocess, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    t = t.replace(' -- ', ' — ')
    return t

def lines(n, cls='lines'):
    return f'<div class="{cls}">' + '<div class="ln"></div>' * int(n) + '</div>'

def render(src):
    out = []; para = []; stack = []
    def flush():
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>'); para.clear()
    L = src.split('\n'); i = 0
    while i < len(L):
        raw = L[i]; s = raw.strip(); i += 1
        if not s: flush(); continue
        if not s.startswith('@'):
            if s.startswith('- '):
                flush(); items = [s[2:]]
                while i < len(L) and L[i].strip().startswith('- '): items.append(L[i].strip()[2:]); i += 1
                out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>'); continue
            if re.match(r'^\d+\.\s', s):
                flush(); items = [re.sub(r'^\d+\.\s', '', s)]
                while i < len(L) and re.match(r'^\d+\.\s', L[i].strip()): items.append(re.sub(r'^\d+\.\s', '', L[i].strip())); i += 1
                out.append('<ol>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ol>'); continue
            para.append(s); flush(); continue
        flush()
        cmd, _, arg = s[1:].partition(' ')
        a = [x.strip() for x in arg.split('|')] if arg else []
        if cmd == 'chapter':
            out.append(f'<section class="chapter"><div class="ch-num">{inline(a[0])}</div><h1>{inline(a[1])}</h1>'
                       + (f'<div class="ch-sub">{inline(a[2])}</div>' if len(a) > 2 else '') + '</section>')
        elif cmd == 'epi':
            out.append(f'<blockquote class="epi">{inline(a[0])}' + (f'<cite>{inline(a[1])}</cite>' if len(a) > 1 else '') + '</blockquote>')
        elif cmd == 'h':
            out.append(f'<h2>{inline(arg)}</h2>')
        elif cmd == 'h3':
            out.append(f'<h3>{inline(arg)}</h3>')
        elif cmd == 'case':
            out.append(f'<div class="case"><div class="case-lbl">{inline(a[0])}</div><h3>{inline(a[1])}</h3>'); stack.append('</div>')
        elif cmd == 'src':
            out.append(f'<div class="src">{inline(arg)}</div>')
        elif cmd == 'ex':
            meta = f'<span class="ex-time">{inline(a[2])}</span>' if len(a) > 2 else ''
            out.append(f'<div class="ex"><div class="ex-top"><div class="ex-head"><span class="ex-code">Задание {inline(a[0])}</span>{meta}</div><h3>{inline(a[1])}</h3>')
            # keep header together with the first paragraph
            first=[]
            if i < len(L) and L[i].strip() and not L[i].strip().startswith('@') and not L[i].strip().startswith('- ') and not re.match(r'^\d+\.\s', L[i].strip()):
                first.append(L[i].strip()); i += 1
            if first: out.append('<p>' + inline(' '.join(first)) + '</p>')
            out.append('</div>'); stack.append('</div>')
        elif cmd == 'note':
            out.append(f'<div class="note"><div class="note-lbl">{inline(arg or "Важно")}</div>'); stack.append('</div>')
        elif cmd == 'end':
            flush(); out.append(stack.pop())
        elif cmd == 'lines':
            out.append(lines(a[0]))
        elif cmd == 'q':  # question + lines
            n = a[1] if len(a) > 1 else 3
            out.append(f'<div class="q">{inline(a[0])}</div>' + lines(n))
        elif cmd == 'box':
            lbl = f'<div class="box-lbl">{inline(a[1])}</div>' if len(a) > 1 else ''
            out.append(f'<div class="box" style="height:{a[0]}mm">{lbl}</div>')
        elif cmd == 'table':
            cols = a; rows = 6; 
            if cols and cols[-1].startswith('rows='): rows = int(cols.pop()[5:])
            head = ''.join(f'<th>{inline(c)}</th>' for c in cols)
            body = ('<tr>' + '<td></td>' * len(cols) + '</tr>') * rows
            out.append(f'<table class="grid"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
        elif cmd == 'ftable':  # filled table: header row then rows via ;;
            rows = [r.split('|') for r in arg.split(';;')]
            head = ''.join(f'<th>{inline(c.strip())}</th>' for c in rows[0])
            body = ''.join('<tr>' + ''.join(f'<td>{inline(c.strip())}</td>' for c in r) + '</tr>' for r in rows[1:])
            out.append(f'<table class="grid filled"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
        elif cmd == 'scale':
            lo = a[1] if len(a) > 1 else '0'; hi = a[2] if len(a) > 2 else '10'
            cells = ''.join(f'<span>{k}</span>' for k in range(int(lo), int(hi) + 1))
            out.append(f'<div class="scale"><div class="scale-lbl">{inline(a[0])}</div><div class="scale-row">{cells}</div></div>')
        elif cmd == 'check':
            items = []
            while i < len(L) and L[i].strip().startswith('- '): items.append(L[i].strip()[2:]); i += 1
            out.append('<ul class="check">' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>')
        elif cmd == 'rate':  # statements with 0-4 boxes
            items = []
            while i < len(L) and L[i].strip().startswith('- '): items.append(L[i].strip()[2:]); i += 1
            rows = ''.join(f'<tr><td class="n">{k+1}</td><td>{inline(x)}</td>' + '<td class="c"></td>' * 5 + '</tr>' for k, x in enumerate(items))
            out.append('<table class="rate"><thead><tr><th></th><th></th><th>0</th><th>1</th><th>2</th><th>3</th><th>4</th></tr></thead><tbody>' + rows + '</tbody></table>')
        elif cmd == 'arrow':  # downward arrow chain of n
            out.append('<div class="arrow">' + '<div class="arr-box"></div><div class="arr">↓ <span>Если это правда — что это значит обо мне?</span></div>' * (int(a[0]) - 1) + '<div class="arr-box core"><span>Ядро:</span></div></div>')
        elif cmd == 'continuum':
            out.append(f'<div class="cont"><div class="cont-lbl">{inline(a[0])}</div><div class="cont-line"><span>0%</span><span>50%</span><span>100%</span></div></div>')
        elif cmd == 'card':  # cut-out card
            out.append(f'<div class="card"><div class="card-lbl">{inline(a[0])}</div>'); stack.append('</div>')
        elif cmd == 'tracker':
            days = int(a[0]); cols = a[1:]
            head = '<th>День</th>' + ''.join(f'<th>{inline(c)}</th>' for c in cols)
            body = ''.join(f'<tr><td class="n">{d}</td>' + '<td></td>' * len(cols) + '</tr>' for d in range(1, days + 1))
            out.append(f'<table class="grid tracker"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
        elif cmd == 'pb':
            out.append('<div class="pb"></div>')
        elif cmd == 'raw':
            out.append(arg)
        elif cmd == 'toc':
            out.append('<!--TOC-->')
        else:
            raise SystemExit(f'unknown directive {cmd} at line {i}')
    flush()
    assert not stack, stack
    return '\n'.join(out)

def main():
    parts = [render(open(f, encoding='utf8').read()) for f in sorted(glob.glob(os.path.join(ROOT, 'content', '*.txt')))]
    body = '\n'.join(parts)
    css = open(os.path.join(ROOT, 'style.css'), encoding='utf8').read()
    fonts = open(os.path.join(ROOT, 'fonts', 'local.css'), encoding='utf8').read()
    doc = f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Дело о дефекте</title><style>{fonts}\n{css}</style></head><body>{body}</body></html>'
    html_path = os.path.join(ROOT, 'workbook.html')
    open(html_path, 'w', encoding='utf8').write(doc)
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'workbook.pdf')
    chrome = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={out}', 'file://' + html_path], check=True, capture_output=True, timeout=300)
    print('ok', out)

if __name__ == '__main__':
    main()
