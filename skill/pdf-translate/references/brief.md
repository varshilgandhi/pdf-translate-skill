# Writer brief - one unit of a PDF into {TARGET_LANGUAGE}

(Orchestrator: copy to <work>/BRIEF.md and replace every {PLACEHOLDER}. Delete the mode section that
does not apply.)

Work dir: {WORK_DIR}
Source PDF: {PDF_PATH}
Your unit's text: `<unit>.txt` in the work dir (pdftotext -layout of your page range).
Approved pilot: {PILOT_FRAGMENT} - READ IT FIRST and match its tone, structure, depth, classes and
vocabulary exactly. The reader has already approved it.

## Reader
{AUDIENCE - who reads it, what for, how comfortable with the target language, e.g. "a
Gujarati-speaking insurance advisor studying for an exam; exam and policies use English terms"}

## Mode: translate
Produce a faithful, COMPLETE translation of your unit into {TARGET_LANGUAGE}.
- Same headings, same order, same lists, same tables, same numbering. Nothing added, nothing dropped,
  nothing summarised. Every sentence's meaning must be present.
- Translate meaning, not word order: the result should read as if written natively in
  {TARGET_LANGUAGE}, in the register of the original (legal stays precise, friendly stays friendly).
- Where the source is ambiguous or clearly wrong, translate it as written and add a short
  translator's note `<span class="tn">[...]</span>`.
- Diagrams/images with text: render the page, look, and reproduce their text as a table or list in
  the same place.

## Mode: study-guide
Produce an independent {TARGET_LANGUAGE} study guide for your unit, in your own words - NOT a
sentence-by-sentence translation (the source is a third party's copyrighted work). It must still be
COMPLETE: every heading, sub-point, number, rule, date, amount, percentage, form/section number,
case name and citation, table and practice-question topic in your range is covered. Then add:
- a few short practical examples (`.box.ex`), clearly framed as examples, never changing facts
- a quick-revision table of 15-40 key facts
- 8-10 NEW multiple-choice questions you write yourself, answers in a box
- a glossary of the terms new in this unit (source term | target-language meaning)
- optional "current position" warn box for time-sensitive facts (laws, rates, regulator names) that
  changed since the source was written - ONLY changes you are highly confident about, saying "for
  exams answer as per the source; verify the latest notification".

## Accuracy rules (both modes)
1. Read the WHOLE .txt. Garbled, tabular or diagram pages: render and look -
   `pdftoppm -r 90 -png -f N -l N "{PDF_PATH}" {WORK_DIR}/look_<unit>_N` then read the image.
2. Numbers, amounts, dates, section/rule/form numbers, codes, formulas, proper names, case names and
   citations: copy EXACTLY. Keep digits as Western digits (0-9) unless the brief says otherwise, so
   they can be checked mechanically.
3. Never invent facts. Source errors (typos, wrong arithmetic, contradictions): keep the source's
   figure and add a short marked note with the correction. Verify arithmetic before calling it wrong.
4. Terminology: use this list consistently (it comes from the approved pilot); target term first,
   source term in `<span class="en">(...)</span>` the first time or where it helps:
   {TERMINOLOGY_LIST}
   Names, citations, codes stay in the source script inside `<span class="en">`.
5. Natural {TARGET_LANGUAGE} a professional would actually speak - not stiff or over-formal.
   Use plain hyphens " - ".
6. Right-to-left languages only: wrap every figure that carries a symbol or separator in `<bdi>` -
   `<bdi>1%</bdi>`, `<bdi>Rs. 2,000</bdi>`, `<bdi>079-4000 1234</bdi>`, `<bdi>Section 80D</bdi>` - or it
   renders reversed ("%1").

## Output format
Write ONE HTML FRAGMENT (no <html>/<head>/<style>) to `{WORK_DIR}/frag_<unit>.html`. Allowed:
h2, h3, h4, p, ul/ol/li, table/thead/tr/th/td, b, i, u, br, `.box`, `.box.warn`, `.box.ex`
(each with `<span class="t">title</span>`), `.en`, `.tn`, `.q`. Structure:

```
<section class="chapter">
<div class="chcover">
  <div class="code">{DOC_CODE} · <SOURCE UNIT LABEL e.g. CHAPTER 3 / ANNEXURE A></div>
  <h1>target-language unit title</h1>
  <div class="sub">source-language title{STUDY_GUIDE_ONLY: · source pages X-Y}</div>
</div>
... content: h2 per major part, h3/h4 below ...
(study-guide only: revision table, optional current-position box, self-test, glossary)
</section>
```
For a part of a split chapter, the chcover says e.g. "(part 2/3)" in the target language.

## Self-check before finishing
- Make a checklist of every heading/sub-heading in the .txt and confirm each is in your fragment.
- Numbers: `python3 {SKILL_DIR}/scripts/qa_pdf.py --numbers {WORK_DIR}/<unit>.txt {WORK_DIR}/frag_<unit>.html`
  lists figures from the source missing in your output. Fix real omissions.
- Validate: `python3 -c "import html.parser,sys;html.parser.HTMLParser().feed(open(sys.argv[1]).read())" <file>`
- Test render: `python3 {SKILL_DIR}/scripts/build_book.py {WORK_DIR}/book.json --only <unit>` and look at
  2-3 page images (`pdftoppm -r 60 -png -f N -l N`) to confirm the script renders and tables fit.

## Reply (short)
Unit, output file, test page count, source word count, numbers-check result, source errors you
flagged, anything you were unsure of. Do not paste the fragment.
