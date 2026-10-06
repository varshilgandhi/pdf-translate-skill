# pdf-translate

A Claude Code skill that turns a whole PDF into a properly typeset PDF in another language.
Books, course material, policy wordings, manuals, reports, even scanned pages.

It was built for an insurance advisor who wanted to learn from a 597-page English book but reads
best in Gujarati. It came back as a 408-page Gujarati study guide, with every table and number kept.

## How it works

1. **Reads every page** and maps the chapters.
2. **Splits the book into units** and writes them in parallel against one shared brief, so the same
   term is translated the same way everywhere.
3. **Checks mechanically:** every page covered, every number from the source present in the output.
4. **Typesets with headless Chrome**, so Indic, Arabic and CJK scripts render correctly
   (conjuncts and right-to-left included), with a cover and a table of contents.

## Languages

Gujarati, Hindi, Marathi, Nepali, Sanskrit, Bengali, Assamese, Punjabi, Odia, Tamil, Telugu,
Kannada, Malayalam, Sinhala, Urdu, Sindhi, Arabic, Persian, Hebrew, Chinese (Simplified and
Traditional), Japanese, Korean, Thai, Lao, Khmer, Burmese, Amharic, Armenian, Georgian, Russian,
Greek, and Latin-script languages such as English, French, Spanish, German, Portuguese, Italian,
Dutch, Turkish, Vietnamese, Indonesian and Swahili. Any language with a Google Noto font can be added
in one line (`skill/pdf-translate/references/languages.md`).

## Install

```sh
cp -r skill/pdf-translate ~/.claude/skills/
# needs poppler-utils, Google Chrome or Chromium, Python 3, and Noto fonts:
sudo apt install poppler-utils fonts-noto fonts-noto-cjk
```

Then in Claude Code: *"Convert this PDF to Gujarati: ~/Downloads/book.pdf"*

## Translation or study guide

If you own the document, it's licensed to you, or it's public (laws, regulations, your own policy
papers), you get a faithful translation. For someone else's copyrighted book, the skill writes a
complete **study guide** in the target language, in its own words, instead of a copy.
Please don't use it to redistribute books you don't have the rights to.

## Cost

It runs on your own Claude plan. A long book is a lot of work, so start with a few chapters.

## License

MIT
