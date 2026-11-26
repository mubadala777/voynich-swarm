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


def extract(epub: Path) -> str:
    paragraphs = []
    with ZipFile(epub) as source:
        for index in range(5, 130):
            chapter = ElementTree.fromstring(source.read(f"OEBPS/c{index:03d}.xhtml"))
            body = chapter.find(f"{XHTML}body")
            for paragraph in body.iter(f"{XHTML}p"):
                if paragraph.get("class") == "sep":
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
