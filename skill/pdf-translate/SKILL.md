---
name: pdf-translate
description: Convert a whole PDF (book, course material, policy wording, manual, report, scanned document) from one language into another and deliver a properly typeset PDF in the target language - Gujarati, Hindi, Marathi, Tamil, Telugu, Kannada, Malayalam, Bengali, Punjabi, Odia, Urdu, Arabic, Chinese, Japanese, Korean, Russian, French, Spanish, German and 100+ more. Handles large documents (hundreds of pages) by splitting into chapters and working in parallel, checks every page is covered and every number survives, and renders complex scripts correctly. Use this whenever someone wants a PDF "in Gujarati / Hindi / <any language>", asks to translate or convert a PDF or book into another language, wants a regional-language version of study material or documents for a family member, client or team, or drops a PDF and names a language - even if they say "convert" rather than "translate", and even for scanned PDFs.
---

# PDF Translate

Turn an English (or any-language) PDF into an accurate, readable PDF in the language the user names.
Proven on a 597-page insurance textbook rendered into a 408-page Gujarati guide.

Core idea: **read every page, split into units, write each unit carefully against a shared brief,
check coverage and numbers mechanically, assemble once, inspect the rendered pages.** Accuracy comes
from the checks, not from hoping the writing was careful.

Scripts live in `scripts/` next to this file (call that dir `$SK`). They need only poppler
(`pdftotext`, `pdftoppm`, `pdfinfo`), Google Chrome / Chromium and Python 3 stdlib.

## Step 0 - Inputs and the rights question

Get: the PDF path, the target language, and what the reader will use it for. Source language is
detected from the text.

Then decide the **mode**. This matters because a full translation of someone else's book is a copy
of that book, and distributing it is not ours to authorise:

| Mode | When | Output |
|---|---|---|
| `translate` | The user or their org owns it, it's licensed / permission given, it's public domain, government law / regulation / circular, the user's own policy documents, forms, letters, manuals for their own product, open-licensed material | Faithful, complete translation, same structure, nothing added or dropped |
| `study-guide` | A third party's copyrighted book or course (publisher, institute, paid course) with no permission | Complete explanation of every page's content in the target language, in our own words, plus revision table, new practice questions, glossary. Not sentence-by-sentence. |

Check the copyright page and source. If it's unclear, ask one short question ("is this your own /
licensed material, or a published book?"). Tell the user which mode you're using and why in one
line, and that `translate` mode becomes available if they get permission. Don't lecture.

Also settle, with sensible defaults rather than a questionnaire:
- **Technical terms**: default is target-language word with the English term in brackets the first
  time, because readers meet the English term in real documents and exams. Legal citations, case
  names, product names, codes and formulas stay as in the source.
- **Audience tone**: plain spoken register a working professional would use, not stiff literary text.

## Size decides the path

- **Small** (under ~6,000 words, roughly 20 pages): do it yourself in one pass - inspect, write one
  fragment per chapter (or one for the whole document), build, QA. Skip the pilot sign-off and the
  parallel writers; show the user the finished PDF instead.
- **Large**: follow every step below. The pilot and the parallel writers are what keep a 500-page job
  accurate and consistent.

## Step 1 - Inspect

```bash
python3 $SK/scripts/inspect_pdf.py <pdf> --out <work>/inspect.json
```
Reports page count, words per page, pages with little or no text (scanned / image pages), pages with
images, the detected heading map (chapters / sections with start pages), and copyright-page hints.
Look at the heading map and fix it by hand if the PDF's headings are unusual (render a page with
`pdftoppm -r 80 -png -f N -l N` and look).

**Scanned or image-only pages**: there is no OCR engine assumed. Render those pages at ~110 dpi and
read them visually; transcribe into `<unit>.txt` before writing. For a mostly-scanned book, make
transcription a separate first pass per unit. If the user mentions an OCR API they have, it can be
used, but read only the specific config variable it needs, never dump an env file.

## Step 2 - Plan units

```bash
python3 $SK/scripts/split_units.py <pdf> <work>/inspect.json --max-words 16000 --out <work>/units.json
```
Splits at chapter boundaries, and splits any chapter above the word budget at its section headings
(e.g. a 51k-word chapter becomes 3 parts). Writes `<work>/<unit>.txt` per unit (`pdftotext -layout`).
~16k source words per unit keeps one writer focused enough to cover every point; much bigger units
start dropping detail.

Edit `units.json` titles: give each unit its target-language title and the source title.
The title / copyright page before the first chapter is not a unit: put its lines on the cover
(`cover` in book.json). If the front matter has real content (preface, foreword), add a unit for it.

## Step 3 - Pilot one unit, get sign-off

Write the first chapter yourself following `references/brief.md`, build it with Step 5, show the user
the PDF, and ask whether the language, the share of English terms, and the depth are right. This is
cheap and saves redoing everything. Fold their answers into the brief.

## Step 4 - Fan out

Copy `references/brief.md` to `<work>/BRIEF.md`, fill in the placeholders (languages, mode, audience,
terminology list taken from the approved pilot, pilot file path). Then launch one subagent per
remaining unit **in a single message** so they run in parallel:

> Follow the brief at `<work>/BRIEF.md` exactly. Your unit: `<id>` (`<source title>`, PDF pages A-B).
> Text file: `<id>.txt`. Output: `frag_<id>.html`.

Each writer self-checks headings coverage, numbers, HTML validity and a test render, and reports book
errors it flagged plus anything it was unsure about. Read every report. When a report says "the book
says X but it should be Y", verify the claim yourself before letting it stand (re-do the arithmetic,
check the source page). When two units disagree on a fact, fix the earlier unit with a note.

## Step 5 - Assemble

Fill in `<work>/book.json` (see `assets/book.example.json`, which documents every key): `mode`
(`translate` or `study-guide`), target language code, title, cover lines, units in order with titles,
optional part headings, and for each unit a `match` string equal to its chcover `.code` line (used to
find page numbers for the contents). For short documents set `"unit_page_break": false` so chapters
don't each start on a fresh, mostly empty page. Then:

```bash
python3 $SK/scripts/build_book.py <work>/book.json
```
Wraps all fragments in the shared stylesheet with the right font stack and text direction for the
language (`references/languages.md`), builds a cover and a table of contents, renders with headless
Chrome, then renders a second time with real page numbers in the contents. Chrome's HarfBuzz shaping
is why Indic and Arabic scripts come out correct; ReportLab-style PDF libraries break conjuncts.

## Step 6 - QA, then deliver

```bash
python3 $SK/scripts/qa_pdf.py <work>/book.json
```
Checks: near-blank pages, that a font for the target script is actually embedded, no fallback "tofu",
and **number coverage per unit** - every figure (amounts, %, section numbers, years, dates) found in
the source unit should appear in its output. Missing numbers are listed per unit; open each one,
and fix real omissions (resume that writer or edit the fragment). In `study-guide` mode, a few
missing numbers that are only page references or list counters are fine.

Then render 6-10 pages across the book (`pdftoppm -r 70`) and look at them: cover, contents, a dense
table, a chapter opening, a page from the last unit. Fix layout problems in CSS, rebuild.

Deliver: the final PDF path (it's the only file the reader needs), page count, size, what's inside,
and a short list of the source's own errors you flagged and anything that is time-sensitive (laws,
rates) the reader should verify. Say plainly whether it's a translation or a study guide.

## Notes that save time

- Big tables: allow them to break across pages by row (the stylesheet does this); "avoid break inside
  table" leaves half-empty pages.
- Forced page breaks before every section waste pages; keep them only before unit openings.
- Keep a single terminology list in the brief so 14 parallel writers use the same word for the same
  concept. Taking it from the approved pilot works best.
- Source books often contain wrong arithmetic, typos in figures, and contradictions between chapters.
  Keep the source figure, add a marked note with the correction - readers may be examined on the
  source text, but must not be misled.
- Time-sensitive content (laws, tax rates, regulator names): an optional "current position" box per
  unit, only for changes the writer is highly confident about, always saying "verify the latest".
- RTL languages (Urdu, Arabic, Persian, Hebrew): the builder sets `dir="rtl"`; keep English terms in
  `<span class="en">` so they render left-to-right inside the line, and wrap figures with symbols,
  phone numbers and codes in `<bdi>` (e.g. `<bdi>1%</bdi>`, `<bdi>079-4000 1234</bdi>`) - otherwise
  "1%" shows as "%1". Look at a page with a table and a percentage before delivering.
- Fonts: the builder binds the target font's Regular and Bold files explicitly (some distros ship a
  Bold file tagged as Regular, which turns a whole book bold). QA warns if only Bold got embedded.
- For readers who will act on the document (clients, customers), use `mode: translate` styling:
  English terms in normal ink, no "source pages" line under chapter titles.
