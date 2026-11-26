"""Read the prose and concluding verse of BDMM LC-001 from the source EPUB."""

import argparse
import hashlib
from pathlib import Path
import re
import unicodedata
from xml.etree import ElementTree
from zipfile import ZipFile


EPUB_SHA256 = "08127876e074c6ab73611de9de85cc03a9dabcbcbe9babbc93391d550887adc8"
XHTML = "{http://www.w3.org/1999/xhtml}"
PARAGRAPH_NUMBER = re.compile(r"^\d+\.\s+")
# These paragraphs contain recognizable marginal variants, printed running
# heads, editorial prose or a photographed library stamp mixed into the OCR.
OMIT_PARAGRAPHS = {
    (12, 2), (12, 12), (14, 2), (15, 5), (19, 2), (24, 3), (37, 1), (38, 1),
    (40, 4), (43, 3), (53, 2), (61, 2), (69, 1), (69, 4), (85, 7), (85, 10), (86, 4),
    (88, 1), (94, 1), (95, 1), (100, 3), (101, 2), (105, 2),
    (105, 6), (107, 1), (113, 366), (121, 9),
}


def extract(epub: Path) -> str:
    paragraphs = []
    with ZipFile(epub) as source:
        for index in range(5, 130):
            chapter = ElementTree.fromstring(source.read(f"OEBPS/c{index:03d}.xhtml"))
            body = chapter.find(f"{XHTML}body")
            for number, paragraph in enumerate(body.iter(f"{XHTML}p"), 1):
                if paragraph.get("class") == "sep" or (index, number) in OMIT_PARAGRAPHS:
                    continue
                text = unicodedata.normalize("NFC", "".join(paragraph.itertext()))
                text = PARAGRAPH_NUMBER.sub("", " ".join(text.split()))
                if text:
                    paragraphs.append(text)
    return "\n\n".join(paragraphs) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("epub", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.epub.read_bytes()).hexdigest() != EPUB_SHA256:
        raise SystemExit("Unexpected BDMM EPUB SHA-256")
    args.output.write_bytes(extract(args.epub).encode("utf-8"))


if __name__ == "__main__":
    main()
