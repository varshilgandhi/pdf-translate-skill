#!/usr/bin/env python3
"""Inspect a PDF before translating: pages, words per page, scanned/image pages, heading map, rights hints.

usage: inspect_pdf.py <pdf> [--out inspect.json]
Needs poppler (pdfinfo, pdftotext, pdfimages).
"""
import argparse, json, re, subprocess, sys
from collections import OrderedDict

HEAD_RE = re.compile(
    r"^\s*(CHAPTER|Chapter|PART|Part|SECTION|Section|ANNEXURE|Annexure|APPENDIX|Appendix|SCHEDULE|Schedule|UNIT|Unit|LESSON|Lesson|MODULE|Module)"
    r"\s+([0-9]{1,3}|[IVXLC]{1,6}|[A-Z])\b")
RIGHTS_RE = re.compile(r"copyright|all rights reserved|©|\bISBN\b|may be reproduced|not be reproduced|creative commons|public domain|licen[cs]e", re.I)


def run(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout


def page_text(pdf, p, layout=False):
    args = ["pdftotext", "-f", str(p), "-l", str(p)] + (["-layout"] if layout else []) + [pdf, "-"]
    return run(*args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out")
    a = ap.parse_args()

    info = run("pdfinfo", a.pdf)
    m = re.search(r"Pages:\s+(\d+)", info)
    if not m:
        sys.exit(f"cannot read {a.pdf}: {info[:200]}")
    n = int(m.group(1))

    img_pages = set()
    for line in run("pdfimages", "-list", a.pdf).splitlines()[2:]:
        parts = line.split()
        if len(parts) > 4 and parts[0].isdigit():
            w, h = int(parts[3]), int(parts[4])
            if w * h > 250_000:  # ignore logos / small header images
                img_pages.add(int(parts[0]))

    pages, headings, rights = [], OrderedDict(), []
    for p in range(1, n + 1):
        t = page_text(a.pdf, p)
        words = len(t.split())
        pages.append({"page": p, "words": words, "chars": len(t.strip()), "big_image": p in img_pages})
        top = [l for l in page_text(a.pdf, p, layout=True).splitlines() if l.strip()][:6]
        for line in top:
            hm = HEAD_RE.match(line.strip())
            after = line.strip()[hm.end():].strip() if hm else ""
            # a heading line is short and is not a sentence that merely starts with "Section 149 (2) ..."
            if hm and len(line.strip()) < 90 and not re.match(r"^[(a-z]", after):
                key = f"{hm.group(1).upper()} {hm.group(2)}"
                if key not in headings:  # first occurrence = start page (running headers repeat it later)
                    title = ""
                    idx = top.index(line)
                    rest = line.strip()[hm.end():].strip(" :-.")
                    title = rest or (top[idx + 1].strip() if idx + 1 < len(top) else "")
                    headings[key] = {"key": key, "start": p, "title_hint": re.sub(r"\s{2,}", " ", title)[:90]}
                break
        if (p <= 12 or p > n - 3) and RIGHTS_RE.search(t):
            rights.append({"page": p, "lines": [l.strip() for l in t.splitlines() if RIGHTS_RE.search(l)][:4]})

    # choose unit-level headings: chapters (+ annexures) if present; PART becomes a grouping only
    all_heads = list(headings.values())
    kind = lambda h: h["key"].split()[0]
    unit_kinds = {"CHAPTER", "UNIT", "LESSON", "MODULE"}
    if any(kind(h) in unit_kinds for h in all_heads):
        keep = unit_kinds | {"ANNEXURE", "APPENDIX", "SCHEDULE"}
    elif any(kind(h) == "PART" for h in all_heads):
        keep = {"PART", "ANNEXURE", "APPENDIX", "SCHEDULE"}
    else:
        keep = {"SECTION", "ANNEXURE", "APPENDIX", "SCHEDULE"}
    groups = [h for h in all_heads if kind(h) == "PART" and "PART" not in keep]
    headings = OrderedDict((h["key"], h) for h in all_heads if kind(h) in keep)

    scanned = [pg["page"] for pg in pages if pg["chars"] < 40 and pg["big_image"]]
    low_text = [pg["page"] for pg in pages if pg["chars"] < 40 and not pg["big_image"]]
    total = sum(pg["words"] for pg in pages)
    sample = " ".join(page_text(a.pdf, p) for p in range(1, min(n, 15) + 1))
    scripts = {
        "latin": len(re.findall(r"[A-Za-z]", sample)),
        "devanagari": len(re.findall(r"[ऀ-ॿ]", sample)),
        "gujarati": len(re.findall(r"[઀-૿]", sample)),
        "arabic": len(re.findall(r"[؀-ۿ]", sample)),
        "cjk": len(re.findall(r"[぀-ヿ一-鿿가-힯]", sample)),
        "cyrillic": len(re.findall(r"[Ѐ-ӿ]", sample)),
    }
    out = {
        "pdf": a.pdf, "pages": n, "total_words": total,
        "script_counts_first_pages": scripts,
        "scanned_pages": scanned, "near_empty_pages": low_text,
        "headings": list(headings.values()),
        "groups": groups,
        "rights_hints": rights,
        "per_page": pages,
    }
    if a.out:
        json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    # human summary
    print(f"pages {n}, words {total}, scanned/image-only pages: {len(scanned)}, near-empty: {len(low_text)}")
    print("dominant script (first pages):", max(scripts, key=scripts.get), scripts)
    print("headings:")
    for h in headings.values():
        print(f"  p{h['start']:>4}  {h['key']:<14} {h['title_hint']}")
    for g in groups:
        print(f"  group p{g['start']:>4}  {g['key']:<14} {g['title_hint']}")
    for r in rights:
        print(f"  rights hint p{r['page']}: {' | '.join(r['lines'])[:160]}")
    if scanned:
        print("scanned pages (render + read visually):", scanned[:40], "..." if len(scanned) > 40 else "")


if __name__ == "__main__":
    main()
