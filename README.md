# Ramon Llull, *Libre de Blanquerna*

Plain UTF-8 text for a historical Catalan reference. Ramon Llull wrote *Libre de Blanquerna* in Catalan around 1283. This export uses the Palma 1914 edition in *Obres de Ramon Llull*, vol. IX, as digitized by the Asociación Cultural Mestre Mateo. The publisher identifies the underlying text as public domain.

- [Biblioteca Dixital Mestre Mateo LC-001, edition and rights statement](https://www.mestremateo.org/en/biblioteca/obras/libre-de-blanquerna.html)
- [Source EPUB](https://www.mestremateo.org/media/biblioteca/obras/libre-de-blanquerna.epub)
- [Palma 1914 edition scan](https://archive.org/details/obresderamonlull09lluluoft)

The export samples the historical prologue, narrative, *Libre de Amic e Amat*, art of contemplation and closing verse. The EPUB's modern front matter, display headings, ornamental separators and leading editorial paragraph numbers were removed. Whitespace was regularized and Unicode normalized to NFC. The export also omits 27 paragraphs containing recognizable printed apparatus, running heads or ornaments interleaved with the text by OCR. `extract.py` lists the exact chapter and paragraph indices. Whole paragraphs were omitted where repair would require guessing word joins. The export has 1,248 paragraphs, 142,739 normalized tokens and 754,252 characters in complete scoring blocks. It has received targeted checks for apparatus and still contains OCR errors.

Run `python3 extract.py libre-de-blanquerna.epub libre-de-blanquerna.txt` from this directory to reproduce the export. The script verifies the input EPUB SHA-256 `08127876e074c6ab73611de9de85cc03a9dabcbcbe9babbc93391d550887adc8`. The plain text SHA-256 is `54a4ab12539d54c375033e6ca7d08cb1fcfc83b353995ee9b37d7ffd8a499753`.
