#!/usr/bin/env python3
"""Assemble unit fragments into one typeset PDF in the target language (cover + TOC with real page numbers).

usage: build_book.py <book.json>            full book -> book.json "output"
       build_book.py <book.json> --only ID  test render of one fragment -> <work>/test_<ID>.pdf
See assets/book.example.json for the config. Renders with headless Chrome (HarfBuzz shaping).
"""
import argparse, html, json, pathlib, re, shutil, subprocess, sys

SK = pathlib.Path(__file__).resolve().parent.parent


def lang_table():
    rows = {}
    for line in (SK / "references/languages.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0] and cells[0] not in ("code", "---") and not cells[0].startswith("-"):
            rows[cells[0]] = {"font": cells[3], "dir": cells[4], "notes": cells[5] if len(cells) > 5 else ""}
    rows.setdefault("latin", {"font": "Noto Sans", "dir": "ltr", "notes": ""})
    return rows


def font_faces(family):
    """Bind the target family's real Regular / Bold files explicitly. Some distros ship a Bold file whose
    metadata claims Regular weight (seen with Noto Nastaliq Urdu), which makes the whole book bold."""
    out = []
    for weight, styles in ((400, ("Regular",)), (700, ("Bold",))):
        files = subprocess.run(["fc-list", f"{family}:style={styles[0]}", "file"], capture_output=True, text=True).stdout.split()
        files = [f.rstrip(":") for f in files if f.rstrip(":").endswith((".ttf", ".otf", ".ttc"))]
        exact = [f for f in files if f.split("/")[-1].replace(" ", "").lower().startswith(family.replace(" ", "").lower() + "-" + styles[0].lower())]
        f = (exact or files or [None])[0]
        src = f"url('file://{f}')" if f else f"local('{family}')"
        out.append(f"@font-face {{ font-family: 'TargetFont'; font-weight: {weight}; src: {src}; }}")
    if not any("url(" in o for o in out):
        print(f"warning: no font file found for '{family}' - install it (fc-list | grep -i '{family}')")
    return "\n".join(out) + "\n"


def chrome():
    for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if shutil.which(c):
            return c
    sys.exit("need google-chrome or chromium for rendering")


def render(html_path, pdf_path):
    r = subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf_path}", f"file://{html_path}"], capture_output=True, text=True)
    if not pathlib.Path(pdf_path).exists():
        sys.exit(f"render failed: {r.stderr[-500:]}")


def page_texts(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    return [subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout
            for p in range(1, n + 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--only")
    a = ap.parse_args()
    cfgp = pathlib.Path(a.config).resolve()
    cfg = json.load(open(cfgp))
    work = (cfgp.parent / cfg.get("work_dir", ".")).resolve()
    L = lang_table()
    lang = cfg.get("lang", "latin")
    if lang not in L:
        print(f"warning: lang '{lang}' not in references/languages.md, using Noto Sans ltr")
    li = L.get(lang, L["latin"])
    font = cfg.get("font") or li["font"]
    direction = cfg.get("dir") or li["dir"]
    tall = any(k in font for k in ("Nastaliq", "Myanmar", "Khmer", "Tamil", "Malayalam"))
    lh = str(cfg.get("line_height") or ("2.3" if "Nastaliq" in font else "1.9" if tall else "1.75"))
    hlh = str(cfg.get("heading_line_height") or ("2.1" if "Nastaliq" in font else "1.6" if tall else "1.4"))
    css = (SK / "assets/style.css").read_text()
    css = (css.replace("__FONT__", f'"TargetFont", "{font}"').replace("__HEADER__", cfg.get("running_header", "").replace('"', "'"))
              .replace("__LH__", lh).replace("__HLH__", hlh)
              .replace("__UNITBREAK__", "page" if cfg.get("unit_page_break", True) else "auto"))
    css = font_faces(font) + css
    if cfg.get("mode", "study-guide") == "translate":
        # source terms are part of the text the reader uses (names, numbers, contacts), not side notes
        css += "\n.en { font-size: 0.95em; color: inherit; }\n"
    css += cfg.get("extra_css", "")

    def frag(uid):
        return (work / f"frag_{uid}.html").read_text()

    def doc(body, title):
        return (f'<!doctype html><html lang="{lang}" dir="{direction}"><head><meta charset="utf-8">'
                f'<title>{html.escape(title)}</title><style>{css}</style></head><body>{body}</body></html>')

    if a.only:
        out = work / f"test_{a.only}.html"
        out.write_text(doc(frag(a.only), a.only))
        pdf = work / f"test_{a.only}.pdf"
        render(out, pdf)
        print(f"{pdf}  pages={len(page_texts(str(pdf)))}")
        return

    units = cfg["units"]
    c = cfg.get("cover", {})

    def build(pages=None):
        rows = []
        for i, u in enumerate(units):
            if u.get("part_heading"):
                rows.append(f'<tr class="part"><td colspan="2">{u["part_heading"]}</td></tr>')
            n = pages[i] if pages else ""
            src = f' <span class="en">({html.escape(u["source_title"])})</span>' if u.get("source_title") else ""
            rows.append(f'<tr><td><b>{u.get("label","")}</b>{" · " if u.get("label") else ""}{u["title"]}{src}</td><td class="n">{n}</td></tr>')
        cover = (f'<section class="cover"><div class="code">{c.get("code","")}</div><h1>{c.get("title", cfg.get("title",""))}</h1>'
                 + "".join(f'<div class="sub">{s}</div>' for s in c.get("subtitles", []))
                 + (f'<div class="note">{c["note"]}</div>' if c.get("note") else "") + "</section>")
        toc = f'<h2>{cfg.get("toc_title","Contents")}</h2><table class="toc">{"".join(rows)}</table>' + cfg.get("after_toc_html", "")
        body = cover + toc + "\n".join(frag(u["id"]) for u in units)
        if cfg.get("footer_note"):
            body += f'<p class="src" style="margin-top:24px">{cfg["footer_note"]}</p>'
        (work / "book.html").write_text(doc(body, cfg.get("title", "")))
        render(work / "book.html", work / "book.pdf")

    def find_pages():
        texts = page_texts(str(work / "book.pdf"))
        starts, p = [], 2
        for u in units:
            needle, extra = u["match"], u.get("match_extra")
            while p <= len(texts):
                t = texts[p - 1]
                p += 1
                if needle in t and (not extra or extra in t):
                    starts.append(p - 1)
                    break
            else:
                starts.append("?")
        return starts, len(texts)

    build()
    pages, _ = find_pages()
    build(pages)
    pages2, total = find_pages()
    out = pathlib.Path(cfg.get("output", "book_final.pdf"))
    out = out if out.is_absolute() else (cfgp.parent / out)
    shutil.copy(work / "book.pdf", out)
    print(f"delivered file: {out}\npages {total}  unit starts {pages2}  {'stable' if pages == pages2 else 'TOC SHIFTED - rerun'}")
    if "?" in pages2:
        print("some units not found in the PDF - check each unit's 'match' text equals its chcover code line")


if __name__ == "__main__":
    main()
