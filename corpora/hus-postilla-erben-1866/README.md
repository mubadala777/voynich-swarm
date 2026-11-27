# Jan Hus, Postilla

This UTF-8 corpus contains the Czech sermons completed in 1413, from the 1866 edition edited by Karel Jaromír Erben and published by Bedřich Tempský in Prague. It uses printed pages 1–427. The closing statement occurs on page 427. Pages 428–434 contain a supplement keyed to reading 46, followed by the index. [Czech National Library edition](https://www.ndk.cz/uuid/3a69fd10-04b1-11dd-abf7-000d606f5dc6) · [Czech Academy source catalogue](https://vokabular.ujc.cas.cz/soubory/essc/essc-soupis-pramenu-a-zkratek.pdf)

The digital library lists the volume and its pages as public. The library defines this category as works in the public domain. The text is derived from the library’s anonymous per-page Kramerius OCR streams. [Rights guidance](https://www.nkp.cz/faq-sluzby-nk-cr) · [Sample stream](https://kramerius5.nkp.cz/search/api/v5.0/item/uuid:dbb91cdf-f997-452e-9a8a-adb57f5aab7f/streams/TEXT_OCR)

The scripts decode each UTF-16 stream, remove the opening title, identifiable running heads, isolated edge numbers, signatures and lines with multiple numbered gloss markers. They also exclude the numbered apparatus on printed page 51 at its scan-verified lines. They join in-page word wraps at hyphens and keep the Czech accents. The result retains OCR errors, running heads or marginalia that the rules missed, and some editorial glosses. It is suitable as an explicitly OCR-derived reference for synthetic controls. An independent set of historical Czech texts would be needed to measure cross-work generalization.

```sh
python3 fetch-nkp-ocr.py --end 427
python3 make-period-corpus.py
```

The page index records the source UUID and scope. The cleaning manifest records the raw OCR digest and removal counts for each page. A change to the library’s OCR can change the resulting file hash.
