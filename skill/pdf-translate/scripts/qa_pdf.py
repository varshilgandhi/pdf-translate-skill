#!/usr/bin/env python3
"""QA for a translated book.

usage: qa_pdf.py <book.json>                       full check of the built PDF + every unit's numbers
       qa_pdf.py --numbers <unit.txt> <frag.html>  numbers check for one unit (writers use this)

Numbers check: every figure in the source unit (amounts, %, years, section/rule/form numbers) should
appear somewhere in the output fragment. Running headers/footers and bare page numbers are ignored.
"""
import argparse, collections, html, json, pathlib, re, subprocess, sys, unicodedata

SK = pathlib.Path(__file__).resolve().parent.parent
NUM = re.compile(r"(?<![\w,])\d+(?:,\d{2,3}(?!\d))*(?:\.\d+)?")  # 1,50,000 / 150,000 / 7.5; "07,2013" splits


def norm(tok):
    t = tok.replace(",", "").rstrip(".")
    if "." in t:
        t = t.rstrip("0").rstrip(".") if re.fullmatch(r"\d+\.\d+", t) else t
    return t


def source_numbers(txt):
    lines = txt.splitlines()
    # drop running headers/footers: lines whose digit-stripped text repeats a lot
    sh = lambda x: re.sub(r"\s+", " ", re.sub(r"\d+", "#", x.strip()))
    shape = collections.Counter(sh(l) for l in lines if l.strip())
    keep = []
    for l in lines:
        s = l.strip()
        if not s or re.fullmatch(r"\d{1,4}", s):
            continue
        if shape[sh(s)] >= 4 and len(s) < 120:
            continue
        keep.append(s)
    found = collections.OrderedDict()
    for s in keep:
        for m in NUM.finditer(s):
            n = norm(m.group())
            unit_after = re.match(r"\s*(%|percent|hours?|hrs?|days?|months?|years?|yrs?|weeks?|am\b|pm\b|lakh|crore|km|kg|cc|minutes?|mins?)", s[m.end():], re.I)
            if len(n.replace(".", "")) < 2 and not unit_after:  # bare single digits are mostly list counters
                continue
            tag = "(answer option) " if re.match(r"^(?:[IVX]{1,4}|[A-Da-d])[.)]\s", s) else ""
            found.setdefault(n, tag + s[:110])
    return found


def output_numbers(frag_html):
    text = html.unescape(re.sub(r"<[^>]+>", " ", frag_html))
    # any script's native digits (Devanagari, Gujarati, Arabic-Indic, Persian, Bengali, Thai ...) -> 0-9
    text = "".join(str(unicodedata.digit(ch)) if ch.isdigit() and not ch.isascii() else ch for ch in text)
    return {norm(m.group()) for m in NUM.finditer(text)}


def numbers_check(txt_path, frag_path, quiet=False):
    src = source_numbers(pathlib.Path(txt_path).read_text())
    out = output_numbers(pathlib.Path(frag_path).read_text())
    missing = [(n, ctx) for n, ctx in src.items() if n not in out]
    cov = 100 * (1 - len(missing) / max(1, len(src)))
    if not quiet:
        print(f"{pathlib.Path(frag_path).name}: {len(src)} source figures, {len(missing)} missing, coverage {cov:.1f}%")
        for n, ctx in missing[:60]:
            print(f"   missing {n:<12} | {ctx}")
        if any("(answer option)" in c for _, c in missing):
            print("   note: '(answer option)' rows are options of the source's own quiz questions - fine to omit in study-guide mode")
        if len(missing) > 60:
            print(f"   ... {len(missing)-60} more")
    return cov, missing


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--numbers":
        numbers_check(sys.argv[2], sys.argv[3])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    a = ap.parse_args()
    cfgp = pathlib.Path(a.config).resolve()
    cfg = json.load(open(cfgp))
    work = (cfgp.parent / cfg.get("work_dir", ".")).resolve()
    pdf = work / "book.pdf"
    if not pdf.exists():
        sys.exit("build first: build_book.py " + a.config)

    sys.path.insert(0, str(SK / "scripts"))
    from build_book import lang_table
    font = cfg.get("font") or lang_table().get(cfg.get("lang", "latin"), {"font": "Noto Sans"})["font"]

    fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
    want = font.replace(" ", "").lower()
    embedded = sorted({l.split()[0].split("+")[-1] for l in fonts.splitlines()[2:] if l.strip()})
    target = [f for f in embedded if f.replace(" ", "").lower().startswith(want)]
    print(f"[font] target '{font}': {', '.join(target) if target else 'NOT EMBEDDED - body text is in a fallback font, fix before delivery'}")
    if target and all("bold" in t.lower() for t in target):
        print("[font] WARNING: only a Bold face of the target font is embedded - body text is probably all bold")
    rest = [f for f in embedded if f not in target]
    print(f"[font] also embedded: {', '.join(rest) or '-'} (normal for Latin terms and a few symbols; look at pages for boxes)")

    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    thin = []
    for p in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(pdf), "-"], capture_output=True, text=True).stdout
        if len(t.strip()) < 200 and p > 2:  # pages 1-2 are cover and contents
            thin.append(p)
    print(f"[pages] {n} pages; near-empty pages: {thin or 'none'} (a short last page of a unit is normal)")

    print("[numbers] per unit:")
    worst = []
    for u in cfg["units"]:
        txt, frag = work / f"{u['id']}.txt", work / f"frag_{u['id']}.html"
        if txt.exists() and frag.exists():
            cov, miss = numbers_check(txt, frag, quiet=True)
            print(f"   {u['id']:<8} coverage {cov:5.1f}%  missing {len(miss)}")
            worst.append((cov, u["id"]))
    if worst:
        print("Inspect the lowest units with: qa_pdf.py --numbers <id>.txt frag_<id>.html")
    out = pathlib.Path(cfg.get("output", "book_final.pdf"))
    out = out if out.is_absolute() else (cfgp.parent / out)
    print(f"Delivered file: {out}")
    print(f"Now render samples and look: pdftoppm -r 70 -png -f N -l N {out} {work}/look")


if __name__ == "__main__":
    main()
