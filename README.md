# Dēnkard, Roman-script Book Pahlavi from Sanjana's edition

This plain UTF-8 corpus contains the Roman-character layer of Dēnkard Books VI–VII from three consecutive volumes of Darab Dastur Peshotan Sanjana's Bombay edition. The diplomatic-style Roman transliteration retains written heterograms. The compendium received its final form around the 10th century and preserves older Zoroastrian material. [Dēnkard, Encyclopaedia Iranica](https://www.iranicaonline.org/articles/denkard/)

| Volume | Imprint | Text covered | Archive scan |
| --- | --- | --- | --- |
| XI | 1910 | Book VI, sections 88–266 | [dinkardoriginalp11pesh](https://archive.org/details/dinkardoriginalp11pesh) |
| XII | 1911 | Book VI, continuing from section 267 | [dinkardoriginalp12pesh](https://archive.org/details/dinkardoriginalp12pesh) |
| XIII | 1912 | End of Book VI and Book VII introduction and chapters I–II | [dinkardoriginalp13pesh](https://archive.org/details/dinkardoriginalp13pesh) |

The title pages give the years listed above. Some library records use 1874, the year the series began. Wikimedia Commons applies the Public Domain Mark 1.0 to each of these scans. [Volume XI](https://commons.wikimedia.org/wiki/File%3AThe_Dinkard._The_original_Pahlavi_text%3B_the_same_transliterated_in_Zend_characters%3B_translations_of_the_text_in_the_Gujrati_and_English_languages_%28IA_dinkardoriginalp11pesh%29.pdf) · [Volume XII](https://commons.wikimedia.org/wiki/File%3AThe_Dinkard._The_original_Pahlavi_text%3B_the_same_transliterated_in_Zend_characters%3B_translations_of_the_text_in_the_Gujrati_and_English_languages_%28IA_dinkardoriginalp12pesh%29.pdf) · [Volume XIII](https://commons.wikimedia.org/wiki/File%3AThe_Dinkard._The_original_Pahlavi_text%3B_the_same_transliterated_in_Zend_characters%3B_translations_of_the_text_in_the_Gujrati_and_English_languages_%28IA_dinkardoriginalp13pesh%29.pdf)

The export uses the scans' embedded OCR. It selects the middle Roman rows on each eligible page, excluding the Pahlavi-script rows, editorial variants, and translations. The extractor verifies the three input PDFs by SHA-256 and writes the page-level selection audit. The selection was spot-checked against the page images. OCR mistakes remain in the Roman letters, accents and word divisions. Three manually read subsets contained about 4–9% normalized character edits against the embedded text, including residual section numbers. That small sample does not estimate accuracy across the corpus.

The text retains Latin accents. The extraction excludes 194 OCR tokens containing letters outside the Roman script and one original-script row verified against the scan. It yields 32,114 normalized words and 183,611 characters in 457 complete scoring blocks.

To reproduce, save the three linked volume PDFs in a directory as `dinkard-xi.pdf`, `dinkard-xii.pdf`, and `dinkard-xiii.pdf`. Run `python3 -B extract.py <scans-directory> dinkard-roman-ocr-xi-xiii.txt` with Python 3.12 and PyMuPDF 1.26.6. The resulting plain text SHA-256 is `c433306b2c249f0efc48e01c9dc2eb899fc8a3213f6f79cb12cf85975f21f663`.
