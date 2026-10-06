#!/usr/bin/env python3
"""Split a PDF into translation units at chapter boundaries; split oversized chapters at section changes.

usage: split_units.py <pdf> <inspect.json> [--max-words 16000] [--first-page N] [--out units.json]
Writes <outdir>/<unit>.txt (pdftotext -layout) for every unit and units.json describing them.
Edit units.json afterwards to set target-language titles or merge/split by hand.
"""
import argparse, json, pathlib, re, subprocess


def text(pdf, a, b, layout=True):
    return subprocess.run(["pdftotext", "-f", str(a), "-l", str(b)] + (["-layout"] if layout else []) + [pdf, "-"],
                          capture_output=True, text=True).stdout


def header_of(pdf, p):
    """Running section header of a page: first non-empty line, digits and chapter labels stripped."""
    for line in text(pdf, p, p).splitlines():
        s = line.strip()
        if s:
            s = re.sub(r"\b(CHAPTER|Chapter|PART|Part|ANNEXURE|Annexure)\s+\S+", "", s)
            s = re.sub(r"[\d]+", "", s)
            return re.sub(r"\s+", " ", s).strip().upper()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("inspect")
    ap.add_argument("--max-words", type=int, default=16000)
    ap.add_argument("--first-page", type=int, help="ignore front matter before this page")
    ap.add_argument("--out", default="units.json")
    a = ap.parse_args()
    ins = json.load(open(a.inspect))
    n = ins["pages"]
    words = {pg["page"]: pg["words"] for pg in ins["per_page"]}
    heads = [h for h in ins["headings"] if not a.first_page or h["start"] >= a.first_page]
    outdir = pathlib.Path(a.out).resolve().parent

    if not heads:  # no headings found - chunk by pages
        heads, per, p = [], 0, (a.first_page or 1)
        start = p
        for q in range(p, n + 1):
            per += words.get(q, 0)
            if per >= a.max_words or q == n:
                heads.append({"key": f"PART {len(heads)+1}", "start": start, "title_hint": ""})
                start, per = q + 1, 0

    ranges = []
    for i, h in enumerate(heads):
        end = heads[i + 1]["start"] - 1 if i + 1 < len(heads) else n
        ranges.append((h, h["start"], end))
    if ranges and ranges[0][1] > 1 and not a.first_page:
        front_words = sum(words.get(p, 0) for p in range(1, ranges[0][1]))
        print(f"note: pages 1-{ranges[0][1]-1} are front matter ({front_words} words) - not included; "
              f"Put the title / author / copyright lines on the cover (book.json 'cover'); add a 'front' unit "
              f"by hand (or rerun with --first-page 1) if it has real content such as a preface.")

    units = []
    for h, s, e in ranges:
        base = re.sub(r"[^a-z0-9]+", "", h["key"].lower().replace("chapter", "ch").replace("annexure", "ann")
                      .replace("appendix", "app").replace("part", "part").replace("section", "sec"))
        total = sum(words.get(p, 0) for p in range(s, e + 1))
        if total <= a.max_words:
            units.append({"id": base, "source_label": h["key"], "source_title": h["title_hint"], "start": s, "end": e, "words": total})
            continue
        # split by running-header sections, packed greedily
        secs, cur, cur_h = [], [s], header_of(a.pdf, s)
        for p in range(s + 1, e + 1):
            hh = header_of(a.pdf, p)
            if hh and hh != cur_h and len(hh) > 3:
                secs.append(cur); cur, cur_h = [p], hh
            else:
                cur.append(p)
        secs.append(cur)
        target = total / max(2, round(total / a.max_words + 0.49))
        parts, acc, accw = [], [], 0
        for sec in secs:
            w = sum(words.get(p, 0) for p in sec)
            if acc and accw + w > target * 1.15:
                parts.append(acc); acc, accw = [], 0
            acc += sec; accw += w
        if acc:
            parts.append(acc)
        for i, pp in enumerate(parts):
            units.append({"id": f"{base}p{i+1}", "source_label": h["key"], "source_title": h["title_hint"],
                          "part": f"{i+1}/{len(parts)}", "start": pp[0], "end": pp[-1],
                          "words": sum(words.get(p, 0) for p in pp)})

    for u in units:
        (outdir / f"{u['id']}.txt").write_text(text(a.pdf, u["start"], u["end"]))
    json.dump({"pdf": a.pdf, "units": units}, open(a.out, "w"), ensure_ascii=False, indent=1)
    for u in units:
        print(f"{u['id']:<8} p{u['start']}-{u['end']:<5} {u['words']:>6}w  {u['source_label']} {u.get('part','')}  {u['source_title']}")


if __name__ == "__main__":
    main()
