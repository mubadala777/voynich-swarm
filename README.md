# Munich Codex (1466), Old Hungarian Gospel text

`munich-codex-1466.txt` is a UTF-8 text export of the four Gospels and the scribal colophon from the Munich Codex (Bayerische Staatsbibliothek, Cod. hung. 1). The codex was copied in 1466. The export preserves the spelling and characters of the HGDS diplomatic transcription. It does not include the calendar, the parallel Latin text from the print edition, or any modern spelling version.

## Sources and rights

- Antal Nyíri, ed., *A Müncheni Kódex 1466-ból*, Budapest, Akadémiai Kiadó, 1971, *Codices Hungarici* 7. [Bibliographic source](https://mek.oszk.hu/08800/08897)
- Eszter Simon, “Corpus building from Old Hungarian codices,” in Katalin É. Kiss, ed., *The Evolution of Functional Left Peripheries in Hungarian Syntax*, Oxford University Press, 2014. The Research Institute for Linguistics of the Hungarian Academy of Sciences hosted the Hungarian Generative Diachronic Syntax project. [HGDS corpus description and requested citation](https://sprakbanken-clarin.lingfil.uu.se/histcorp/readme/hungarian-readme-HGDS)
- Eva Pettersson, *The HistCorp Collection of Historical Corpora and Resources – Part II*, DOI `10.5281/zenodo.10017218`. HistCorp identifies this file as HGDS text with a metadata header added. The archived distribution is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Distribution licence record](https://api.datacite.org/dois/10.5281/zenodo.10017218) · [Download](https://zenodo.org/records/10017218/files/hungarian-HGDS-txt.zip?download=1)
- The Bayerische Staatsbibliothek provides the manuscript scans and catalogue. [Cod. hung. 1](https://www.digitale-sammlungen.de/en/details/bsb00087531)

This body-only export derives from the member `hungarian/HGDS/txt/1466-MunchK_orig.txt` of `hungarian-HGDS-txt.zip`. The archive SHA-256 is `98aecf22817ea3548e30a455f02438cd027fa2abeea63f89d42d8644390f02bb`. The archived member SHA-256 is `b6b8a3084ee17be501b27e5d51c1abc3939af2a3275cebdd0f029255a46f7724`. The export remains under CC BY 4.0. See `extract.py` for the exact preparation.

After downloading the ZIP from HistCorp, reproduce the plain text with `python3 extract.py hungarian-HGDS-txt.zip munich-codex-1466.txt`.

The export removes the HistCorp metadata header and 416 folio and column markers. It regularizes horizontal spacing within lines and preserves the remaining transcription, including editorial marks and abbreviations. The Old Hungarian reference normalizer yields 58,192 word tokens and 353,997 characters in complete blocks of about 400 characters. These figures describe this biblical witness alone.
