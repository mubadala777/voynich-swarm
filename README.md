# Ramon Llull, *Libre de Blanquerna*

Plain UTF-8 text for a historical Catalan reference. Ramon Llull wrote *Libre de Blanquerna* in Catalan around 1283. This export uses the Palma 1914 edition in *Obres de Ramon Llull*, vol. IX, as digitized by the Asociación Cultural Mestre Mateo. The publisher identifies the underlying text as public domain.

- [Biblioteca Dixital Mestre Mateo LC-001, edition and rights statement](https://www.mestremateo.org/en/biblioteca/obras/libre-de-blanquerna.html)
- [Source EPUB](https://www.mestremateo.org/media/biblioteca/obras/libre-de-blanquerna.epub)
- [Palma 1914 edition scan](https://archive.org/details/obresderamonlull09lluluoft)

The export includes the historical prologue, narrative, *Libre de Amic e Amat*, art of contemplation and closing verse. The EPUB's modern front matter, display headings, ornamental separators and leading editorial paragraph numbers were removed. Whitespace was regularized and Unicode normalized to NFC. The digitization uses OCR and editorial review. Some OCR errors remain. The export has 1,275 paragraphs, 148,545 normalized tokens and 783,932 characters in complete scoring blocks.

Run `python3 extract.py libre-de-blanquerna.epub libre-de-blanquerna.txt` from this directory to reproduce the export. The script verifies the input EPUB SHA-256 `08127876e074c6ab73611de9de85cc03a9dabcbcbe9babbc93391d550887adc8`. The plain text SHA-256 is `74921f21f1c15b85182a1a6367cfb90a12afe742b30c16a8d008631e8c777576`.
