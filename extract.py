"""Extract the four old Hungarian Gospels from a pinned HistCorp release.

Source: https://doi.org/10.5281/zenodo.10017218 (CC BY 4.0).
See the package README for the author of the original corpus and its citation.
"""

import argparse
import hashlib
import re
from pathlib import Path
from zipfile import ZipFile


ARCHIVE_SHA256 = "98aecf22817ea3548e30a455f02438cd027fa2abeea63f89d42d8644390f02bb"
MEMBER = "hungarian/HGDS/txt/1466-MunchK_orig.txt"
MEMBER_SHA256 = "b6b8a3084ee17be501b27e5d51c1abc3939af2a3275cebdd0f029255a46f7724"
FOLIO = re.compile(r"\{ó?\d+[rv][ab]\}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()

    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("Unexpected HistCorp archive SHA-256")
    with ZipFile(args.archive) as archive:
        raw = archive.read(MEMBER)

    if hashlib.sha256(raw).hexdigest() != MEMBER_SHA256:
        raise SystemExit("Unexpected Munich Codex member SHA-256")

    metadata, separator, body = raw.decode("utf-8").partition("\n\n")
    if not separator or not all(line.startswith("# ") for line in metadata.splitlines()):
        raise SystemExit("Expected the HistCorp metadata block")
    body = body.strip()
    if not body.startswith("{8ra}") or "{108rb}" not in body:
        raise SystemExit("Expected Gospels and colophon, folios 8ra through 108rb")

    body, markers = FOLIO.subn(" ", body)
    if markers != 416:
        raise SystemExit(f"Expected 416 folio-column markers, found {markers}")

    # Preserve the diplomatic transcription, including editorial spelling marks.
    lines = (re.sub(r"[ \t]+", " ", line).strip() for line in body.splitlines())
    data = ("\n".join(lines) + "\n").encode("utf-8")
    args.out.write_bytes(data)
    print(f"{len(data)} bytes, SHA-256 {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
