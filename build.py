#!/usr/bin/env python3
# Генератор статического сайта «База эскизов татуировок» (только тексты; без картинок)
import os, re, html, csv, io, json

BASE = "/home/alexdev/Tattoo_Study_Base"
OUT  = "/home/alexdev/tattoo_html"

# ---------- конфигурация разделов (key, name, читается из папок) ----------
NAV = [
    ("index", "Главная"),
    ("start", "Старт"),
    ("kanji", "Иероглифы"),
    ("fonts", "Шрифты"),
    ("beginner", "Практика новичку"),
    ("body", "Посадка на тело"),
    ("tonal", "Тон"),
    ("refs", "Эскизы и цвет"),
    ("flash", "Флеш-идеи"),
    ("books", "Учёба"),
    ("reviews", "Рецензии"),
]

# папка-источник для каждого контентного раздела
SRC = {
    "start":    "00_QuickStart",
    "beginner": "06_Tattoo_Beginners_Guide",
    "body":     "07_Body_Mapping",
    "tonal":    "08_Tonal_Studies",
    "refs":     "02_Realism_Refs",
    "flash":    "09_Flash_Traditional",
    "books":    "04_Books",
}

# файлы README про SVG-эскизы — это про картинки, исключаем целиком
SKIP_WHOLE = {
    "02_Realism_Refs/Орнаментал_SVG/README.txt",
    "02_Realism_Refs/Minimal_FineLine/README.txt",
}

IMG_RE    = re.compile(r"\.(jpe?g|png|gif|webp|bmp|svg|tif|tiff|psd)", re.I)
IMG_WORDS = re.compile(
    r"(см\.?\s*)?(картинк|иллюстраци|превью|фото|\bрис[а-яё]*\b|cмотрим?\s+(фото|эскиз)\b|cм\.\s*(фото|эскиз|картинк))\.?",
    re.I)

def clean_text(raw):
    out = []
    for ln in raw.split("\n"):
        if IMG_RE.search(ln):          # упоминание файла-картинки
            continue
        if IMG_WORDS.search(ln):       # словесное упоминание
            continue
        out.append(ln)
    return "\n".join(out)

def esc(t):
    return html.escape(t)

def page(title, body, active, with_fonts=False):
    nav = "\n".join(
        f'<a href="{k}.html"{" class=\"on\"" if k==active else ""}>{n}</a>'
        for k, n in NAV)
    fcss = '<link rel="stylesheet" href="css/fonts.css">' if with_fonts else ""
    return f"""<!DOCTYPE html>
<html lang=\"ru\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>{esc(title)} — База эскизов татуировок</title>
<link rel=\"stylesheet\" href=\"css/main.css\">
{fcss}
</head>
<body>
<div class=\"topbar\">
  <span class=\"logo\">База тату-эскизов</span>
  <nav>{nav}</nav>
</div>
<div class=\"wrap\">
{body}
<footer>Учебная база для начинающего тату-мастера. Без картинок — только тексты, иероглифы и шрифты.</footer>
</div>
</body>
</html>
"""

def h1(t): return f"<h1>{esc(t)}</h1>"

def txt_block(path, title=None):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    c = clean_text(raw).strip()
    if not c:
        return ""
    title = title or os.path.splitext(os.path.basename(path))[0]
    body = esc(c).replace("\n", "<br>")
    return f"<div class=\"card\"><h3>{esc(title)}</h3><p class=\"txt\">{body}</p></div>"

def section_page(key, name, subtitle, intro_files, folder=None):
    parts = [h1(name)]
    if subtitle:
        parts.append(f"<div class=\"sub\">{esc(subtitle)}</div>")
    # интро-файлы из корня базы
    for f in intro_files:
        p = os.path.join(BASE, f)
        if os.path.isfile(p):
            b = txt_block(p)
            if b: parts.append(b)
    # все txt/md из папки раздела
    if folder:
        import glob
        files = []
        for dp, _, fs in os.walk(os.path.join(BASE, folder)):
            for fn in sorted(fs):
                if fn.lower().endswith((".txt", ".md")):
                    rel = os.path.join(folder, os.path.relpath(dp, BASE), fn).replace("./", "")
                    if rel in SKIP_WHOLE:
                        continue
                    files.append(os.path.join(dp, fn))
        files.sort()
        for p in files:
            b = txt_block(p)
            if b: parts.append(b)
    return "\n".join(parts)

def build():
    os.makedirs(OUT, exist_ok=True)

    # ---------- отражаем конкретный текст разделов ----------
    # СТАРТ: корень + 00_QuickStart
    st = [h1("Старт")] + [
        "<div class='sub'>Первые 3 действия, план уровней и календарь на 30 дней. Начинай здесь.</div>"]
    for f in ["START_HERE.txt", "LEVEL_MAP.txt", "00_Checklists.txt", "INKS-NEEDLES.txt"]:
        b = txt_block(os.path.join(BASE, f))
        if b: st.append(b)
    for dp, _, fs in os.walk(os.path.join(BASE, "00_QuickStart")):
        for fn in sorted(fs):
            if fn.lower().endswith((".txt", ".md")):
                b = txt_block(os.path.join(dp, fn))
                if b: st.append(b)
    write("start.html", page("Старт", "\n".join(st), "start"))

    # КАНДЗИ: из words.csv (без картинок)
    kj = [h1("Иероглифы"), "<div class='sub'>32 значения для эскиза — упрощённая и традиционная формы, пояснение значения.</div>"]
    cards = []
    with open(os.path.join(BASE, "05_Kanji_Letters", "words.csv"), encoding="utf-8", newline="") as f:
        rd = list(csv.reader(f))[1:]
    for r in rd:
        while len(r) < 4:
            r.append("")
        ru, simp, trad, note = r[0], r[1], r[2], r[3]
        cards.append(
            "<div class='k-card'>"
            f"<div class='k-glyph'>{esc(simp)}</div>"
            "<div><div class='k-title'>" + esc(ru) + "</div>"
            f"<div class='k-trad'><b>традиц.:</b> <span class='jb'>{esc(trad)}</span></div>"
            + (f"<div class='k-note'>{esc(note)}</div>" if note else "")
            + "</div></div>")
    kj.append("<div class='grid-k'>" + "\n".join(cards) + "</div>")
    kj.append("<div class='note danger'><b>Важно:</b> всегда сверяй перевод перед нанесением. Ошибочный иероглиф может означать не то слово.</div>")
    write("kanji.html", page("Иероглифы", "\n".join(kj), "kanji"))

    # ШРИФТЫ: 63 web-font
    fonts = json.load(open("/home/alexdev/tattoo_html_data_fonts.json"))
    def fam(n): return "t-" + re.sub(r"[^a-z0-9]", "-", n)
    ft = [h1("Шрифты"), "<div class='sub'>63 гарнитуры для надписей. Превью показывается реальными шрифтами; лицензии помечены.</div>"]
    grid = []
    for x in fonts:
        fname = x["file"].rsplit(".", 1)[0].lower()
        lic = x["license"]
        liccls = "lic-fr" if "free (лич)" not in lic else "lic-pe"
        liclbl = "личн." if "лич" in lic else "своб."
        if lic == "OFL":
            liccls, liclbl = "lic-of", "OFL"
        grid.append(
            "<div class='f-card'>"
            f"<div class='f-prev' style='--fa: \"{fam(fname)}\"'>АБВ абв 123</div>"
            f"<div class='f-name'>{esc(x['name'])}</div>"
            f"<div class='f-meta'>{esc(x['file'])} · <span class='lic {liccls}'>{liclbl}</span></div>"
            f"<a class='f-dl' href='fonts/{fname}.woff2' download>скачать .woff2</a>"
            "</div>")
    ft.append("<div class='grid-f'>" + "\n".join(grid) + "</div>")
    ft.append("<div class='note warn'><b>Лицензии:</b> шрифты с пометкой \"личн.\" предназначены для личного использования. Для коммерческих работ (за деньги в студии) используй только свободные (OFL и \"своб.\").</div>")
    write("fonts.html", page("Шрифты", "\n".join(ft), "fonts", with_fonts=True))

    # Остальные разделы — авто
    for key, name in [("beginner","Практика новичку"),("body","Посадка на тело"),
                      ("tonal","Тон"),("refs","Эскизы и цвет"),("flash","Флеш-идеи"),
                      ("books","Учёба")]:
        body = section_page(key, name, "", [], SRC[key])
        write(key + ".html", page(name, body, key))

    # РЕЦЕНЗИИ
    rv = [h1("Рецензии"), "<div class='sub'>Что сказали ИИ о базе после финальной проверки. Поправки уже внесены — здесь только итоговые вердикты.</div>"]
    def quote(author, role, verdict, cls="lic-fr"):
        return ("<div class='card'>"
                f"<div style='font-style:italic;color:#d9d9e6'>{esc(verdict)}</div>"
                f"<div style='margin-top:8px;color:#fff;font-weight:600'>{esc(author)}</div>"
                f"<div style='font-size:.82rem;color:#9a9ab0'>{esc(role)}</div></div>")
    rv.append(quote(
        "GigaChat (Сбер)",
        "финальный валидатор",
        "База готова к вручению: 1900+ файлов, всё собрано и проверено. Поправки из рецензии внесены — остаётся только вручить подарок.",
        "lic-fr"))
    rv.append(quote(
        "DeepSeek",
        "финальный валидатор",
        "Финальная оценка 9.8/10. Мелкие пробелы закрыты, база завершена. Все замечания внедрены.",
        "lic-fr"))
    rv.append(quote(
        "qwen",
        "валидатор «последней мили»",
        "Готовность 99%. Цепочка валидации завершена, осталось вручить.",
        "lic-fr"))
    rv.append(quote(
        "YandexGPT (Алиса)",
        "валидатор",
        "Круг валидации замкнулся — замечания внедрены, база собрана.",
        "lic-fr"))
    rv.append(quote(
        "opencode",
        "мультиагентная модель с инструментами, анализатор и исполнитель",
        "Это не папка с картинками, а выстроенная система обучения: уровни, календарь, инструменты, документы и дисциплина. База — не «собрана», а доведена до готовности: наполнена, отлажена, перепроверена пятью моделями и приведена к одному честному комплекту. Вручаешь — и человек получает не разрозненные файлы, а готовый маршрут от первого штриха до первой студийной работы.",
        "lic-fr"))
    rv.append(quote(
        "Саша",
        "соавтор и советник",
        "Помогал, советовал и решал, что оставить, а что убрать.",
        "lic-fr"))
    write("reviews.html", page("Рецензии", "\n".join(rv), "reviews"))
    print("Готово:", sorted(os.listdir(OUT)))

def write(fn, s):
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        f.write(s)

if __name__ == "__main__":
    build()