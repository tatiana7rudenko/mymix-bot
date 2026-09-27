"""Собирает research/10_digest.md из файлов агентов: сквозная нумерация, ранжирование."""
import re
from pathlib import Path

R = Path(__file__).parent


def split_numbered(text, level):
    """Находки вида '## N. Заголовок' (или ###). Ненумерованный заголовок того же/высшего уровня обрывает блок."""
    hashes = "#" * level
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(rf"^{hashes} (\d+)\. (.+)$", line)
        if m:
            cur = int(m.group(1))
            out[cur] = [m.group(2).strip(), []]
            continue
        if re.match(rf"^#{{1,{level}}} ", line):
            cur = None
            continue
        if cur is not None:
            out[cur][1].append(line)
    return {k: (t, clean(b)) for k, (t, b) in out.items()}


def clean(lines):
    body = "\n".join(lines).strip()
    body = re.sub(r"(\n\s*---\s*)+$", "", body).strip()
    return body


def books():
    text = (R / "06_books.md").read_text()
    out, book, idea = {}, None, None
    for line in text.splitlines():
        m = re.match(r"^### (\d+)\. (.+)$", line)
        if m:
            book, idea = int(m.group(1)), None
            name = m.group(2)
            continue
        if line.startswith("## "):
            book = idea = None
            continue
        m = re.match(r"^\*\*Идея (\d+)\. (.+?)\*\*\s*$", line)
        if m and book:
            idea = int(m.group(1))
            author = name.split(" — ")[0].split(" (")[0]
            t = re.search(r"«[^»]+»", name)
            out[(book, idea)] = [f"{m.group(2)} ({author}, {t.group(0) if t else name.split(' — ')[-1]})", [], name]
            continue
        if book and idea and line.strip() != "---":
            out[(book, idea)][1].append(line)
    return {k: (t, f"*Книга: {n}*\n\n" + clean(b)) for k, (t, b, n) in out.items()}


def big_ideas():
    text = (R / "04_big_ideas.md").read_text()
    ideas = split_numbered(text, 3)
    m = re.search(r"## Шаг 1\.[^\n]*\n(.*?)\n## Шаг 2", text, re.S)
    items = [re.sub(r"^\d+\.\s*", "", l).strip() for l in m.group(1).splitlines() if re.match(r"^\d+\.", l)]
    ideas["map"] = ("Карта заезженного: 40 советов про «энергии», которые аудитория слышит из каждого утюга",
                    "Это список формулировок, советов и углов подачи, которые давно заезжены в теме «мужской и женской энергии» и вызывают у аудитории реакцию «опять это». Он собран по коучинговым сайтам, соцсетям и критическим статьям и служит фоном: на нём видно, что в теме действительно ново.\n\n"
                    + "\n".join(f"- {i}" for i in items))
    return ideas


SECTIONS = [
    ("Наука: что на самом деле известно про «мужское» и «женское» в людях", "05_science.md", 2,
     [7, 6, 13, 14, 19, 4, 1, 16, 17, 11, 12, 15, 8, 9, 10, 3, 18, 20, 2, 5]),
    ("Большие идеи: как «энергии» переводят на нормальный язык (начало волны)", "04", 3,
     [1, 2, 6, 5, 3, 4, 17, 8, 9, 13, 14, 7, 23, 15, 16, 18, 21, 20, 19, 12, 10, 22, 11, 24, 25, "map"]),
    ("Практики и упражнения: провести с аудиторией или дать домой", "09_practices.md", 3,
     [5, 1, 4, 2, 6, 7, 16, 22, 17, 8, 14, 15, 13, 11, 10, 12, 18, 9, 3, 19, 20, 21]),
    ("Книги: откуда вырос термин и чем его разобрать", "06", None,
     [(1, 2), (1, 1), (1, 4), (1, 3)]),
    ("Яркие истории", "07_stories.md", 2,
     [16, 17, 11, 12, 4, 1, 2, 3, 5, 14, 15, 13, 10, 9, 8, 6, 7, 18]),
    ("Известные люди и компании", "08_celebrities.md", 2,
     [12, 7, 6, 1, 3, 4, 14, 8, 5, 2, 16, 15, 17, 13, 9, 10, 11]),
    ("Мировые рынки: что продают под «энергией» в других странах", "03_foreign.md", 2,
     [16, 1, 9, 8, 3, 4, 17, 10, 13, 6, 5, 12, 14, 7, 2, 11, 15, 18]),
    ("Что взорвало соцсети за последний год", "01_trends.md", 2,
     [5, 9, 10, 1, 2, 3, 8, 6, 7, 4, 12, 13, 14, 15, 11, 16]),
    ("Новости: суды, скандалы, опросы", "02_news.md", 2,
     [1, 4, 3, 2, 7, 5, 6, 8, 9]),
]
BOOK_ORDER = [8, 10, 9, 11, 6, 5, 3, 2, 13, 12, 7, 4, 14]


def main():
    intro = (R / "digest_intro.md").read_text()
    parts = [intro.rstrip(), ""]
    n = 0
    for title, src, level, order in SECTIONS:
        if src == "04":
            items = big_ideas()
        elif src == "06":
            items = books()
            order = order + [k for b in BOOK_ORDER for k in sorted(items) if k[0] == b]
        else:
            items = split_numbered((R / src).read_text(), level)
        missing = set(items) - set(order)
        assert not missing, (src, missing)
        parts += ["---", "", f"## {title}", ""]
        for k in order:
            n += 1
            t, body = items[k]
            parts += [f"### №{n}. {t}", "", body, ""]
    (R / "10_digest.md").write_text("\n".join(parts))
    print("findings:", n)


main()
