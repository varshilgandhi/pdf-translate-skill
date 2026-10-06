# Language settings

`build_book.py` reads this table (the `code` column) to pick the font stack and direction.
Fonts are Google Noto (install `fonts-noto`, `fonts-noto-cjk` on Debian/Ubuntu if missing; check with
`fc-list | grep -i "<family>"`). Any language whose script has a Noto font works - add a row.

| code | language | script | font family (body) | dir | notes |
|---|---|---|---|---|---|
| gu | Gujarati | Gujarati | Noto Sans Gujarati | ltr | conjuncts need HarfBuzz (Chrome) |
| hi | Hindi | Devanagari | Noto Sans Devanagari | ltr | |
| mr | Marathi | Devanagari | Noto Sans Devanagari | ltr | |
| ne | Nepali | Devanagari | Noto Sans Devanagari | ltr | |
| sa | Sanskrit | Devanagari | Noto Serif Devanagari | ltr | |
| bn | Bengali | Bengali | Noto Sans Bengali | ltr | |
| as | Assamese | Bengali | Noto Sans Bengali | ltr | |
| pa | Punjabi | Gurmukhi | Noto Sans Gurmukhi | ltr | |
| or | Odia | Oriya | Noto Sans Oriya | ltr | |
| ta | Tamil | Tamil | Noto Sans Tamil | ltr | long words - slightly smaller body size |
| te | Telugu | Telugu | Noto Sans Telugu | ltr | |
| kn | Kannada | Kannada | Noto Sans Kannada | ltr | |
| ml | Malayalam | Malayalam | Noto Sans Malayalam | ltr | |
| si | Sinhala | Sinhala | Noto Sans Sinhala | ltr | |
| ur | Urdu | Arabic (Nastaliq) | Noto Nastaliq Urdu | rtl | tall line height (2.2+) |
| sd | Sindhi | Arabic | Noto Naskh Arabic | rtl | |
| ar | Arabic | Arabic | Noto Naskh Arabic | rtl | |
| fa | Persian | Arabic | Noto Naskh Arabic | rtl | |
| he | Hebrew | Hebrew | Noto Sans Hebrew | rtl | |
| zh | Chinese (Simplified) | Han | Noto Sans CJK SC | ltr | no word spaces; justify off |
| zh-Hant | Chinese (Traditional) | Han | Noto Sans CJK TC | ltr | |
| ja | Japanese | Kana/Kanji | Noto Sans CJK JP | ltr | |
| ko | Korean | Hangul | Noto Sans CJK KR | ltr | |
| th | Thai | Thai | Noto Sans Thai | ltr | no word spaces |
| lo | Lao | Lao | Noto Sans Lao | ltr | |
| km | Khmer | Khmer | Noto Sans Khmer | ltr | |
| my | Burmese | Myanmar | Noto Sans Myanmar | ltr | |
| am | Amharic | Ethiopic | Noto Sans Ethiopic | ltr | |
| hy | Armenian | Armenian | Noto Sans Armenian | ltr | |
| ka | Georgian | Georgian | Noto Sans Georgian | ltr | |
| ru | Russian | Cyrillic | Noto Sans | ltr | also uk, bg, sr, kk |
| el | Greek | Greek | Noto Sans | ltr | |
| en | English | Latin | Noto Sans | ltr | also fr, es, de, it, pt, nl, sv, pl, tr, vi, id, ms, sw, tl ... |

For any Latin/Cyrillic/Greek language not listed, use code `latin` (Noto Sans, ltr).

Digits: keep Western digits 0-9 in the output by default (makes number QA mechanical and matches
legal/financial documents). Only switch to native digits if the reader explicitly wants them, and
then skip the numbers check.
