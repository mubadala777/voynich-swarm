"""Conservative UTF-8 extract of the Erben edition of Hus's Czech Postilla."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata


ROOT = Path(__file__).resolve().parent
LETTERS = "abcdefghijklmnopqrstuvwxyzáčďéěíňóřšťúůýž"
UPPER = LETTERS.upper()
ALLOWED = set(LETTERS + UPPER + ",.;:!?-'’\u2010\u2013\u2014()[]„“”\" ")
PAGE_MARK = re.compile(r"^\s*[\d*]{1,5}\s*$")
NUMBERED_GLOSS = re.compile(r"(?<!\w)\d{1,2}\)")
BOOK_SIGNATURE = re.compile(r"^\s*M\.\s*J\.\s*H", re.IGNORECASE)
AUDITED_GLOSS_BLOCKS = {51: (15, 24)}
CZECH_HEAD = re.compile(
    r"^\s*(?:\d+\s*)?(?:Čten[iíe]|N[eé]d[eě]l[eě]|Ned[ilí]l[aá]|"
    r"Na posv[eě]c|V [úu]ter[ýy] po|Na den |Svat[ýy]ch )", re.IGNORECASE)
BODY_START = 1
BODY_END = 427


def raw_text(path):
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def normalized_czech(body):
    deaccented = unicodedata.normalize("NFKD", body.lower())
    folded = "".join(ch for ch in deaccented if not unicodedata.combining(ch))
    return re.sub(r"[^a-z]+", " ", folded).strip()


def trim_page(page, raw):
    lines = [unicodedata.normalize("NFC", line).strip() for line in raw.splitlines() if line.strip()]
    removed = Counter()
    if page in AUDITED_GLOSS_BLOCKS:
        first_gloss, body_resume = AUDITED_GLOSS_BLOCKS[page]
        lines[first_gloss:body_resume] = [""] * (body_resume - first_gloss)
        removed["scan_checked_gloss_block_lines"] += body_resume - first_gloss
    if page == BODY_START:
        if len(lines) > 23 and lines[23].endswith("mluviti in um"):
            lines[23] = lines[23].removesuffix(" in um")
            removed["scan_checked_marginal_spans"] += 1
        del lines[:2]  # printed title and subtitle, confirmed on the scan
        removed["title_lines"] += 2
    elif page == 51 and lines:
        del lines[0]  # scan-verified running head; its page number was mangled
        removed["running_headers"] += 1
    elif lines and len(lines[0]) < 70:
        first = lines[0]
        has_print_number = re.search(fr"(?:^|\s){page}(?:\s|$)", first)
        if has_print_number or CZECH_HEAD.match(first):
            del lines[0]
            removed["running_headers"] += 1
    retained = []
    for index, line in enumerate(lines):
        if index >= len(lines) - 3 and BOOK_SIGNATURE.match(line):
            removed["book_signatures"] += 1
            retained.append("")
        elif PAGE_MARK.fullmatch(line) and (index < 2 or index >= len(lines) - 3):
            removed["isolated_numbers_at_edges"] += 1
            retained.append("")
        elif len(NUMBERED_GLOSS.findall(line)) >= 2:
            removed["unambiguous_gloss_lines"] += 1
            retained.append("")
        else:
            retained.append(line)
    text = "\n".join(retained)
    cleaned = re.sub(fr"([{LETTERS}{UPPER}])[-\u2010]\n(?=[{LETTERS}])", r"\1", text)
    removed["joined_letter_hyphen_line_ends"] = text.count("\n") - cleaned.count("\n")
    cleaned = "".join(ch if ch in ALLOWED else " " for ch in cleaned)
    cleaned = re.sub(r" +", " ", cleaned).strip()
    return cleaned, removed


def summarize_raw(root, end):
    manifest, segments, cumulative = [], [], Counter()
    for page in range(BODY_START, end + 1):
        path = root / f"{page:03}.txt"
        if not path.is_file():
            continue
        raw = raw_text(path)
        if "\ufffd" in raw:
            raise ValueError(f"Unrecoverable byte corruption on page {page}")
        clean, removed = trim_page(page, raw)
        normalized = normalized_czech(clean)
        segments.append(clean)
        manifest.append({
            "page": page, "source_bytes_sha256": sha256(path.read_bytes()).hexdigest(),
            "raw_normalized_characters": len(normalized_czech(raw)),
            "clean_normalized_characters": len(normalized),
            "clean_tokens_after_normalization": len(normalized.split()),
            "removed": dict(removed), "remaining_numbered_gloss_lines_in_source": sum(
                len(NUMBERED_GLOSS.findall(line)) == 1 for line in raw.splitlines()),
        })
        cumulative.update(removed)
    text = "\n\n".join(segments) + "\n"
    summary = {
        "edition": "Karel Jaromír Erben, Sebrané spisy české II, Prague, 1866",
        "source": "Czech National Library, NDK edition 3a69fd10-04b1-11dd-abf7-000d606f5dc6",
        "minimum_printed_page": BODY_START, "maximum_printed_page": end,
        "available_printed_pages": len(manifest),
        "missing_printed_pages": sorted(set(range(BODY_START, end + 1)) - {row["page"] for row in manifest}),
        "corpus_bytes": len(text.encode("utf-8")),
        "normalized_characters": len(normalized_czech(text)),
        "normalized_tokens": len(normalized_czech(text).split()),
        "raw_normalized_characters_sum": sum(row["raw_normalized_characters"] for row in manifest),
        "remaining_numbered_gloss_lines_in_source": sum(row["remaining_numbered_gloss_lines_in_source"] for row in manifest),
        "removed": dict(cumulative),
        "utf8_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "page_manifest": manifest,
    }
    return text, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end", type=int, default=BODY_END)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    result, info = summarize_raw(ROOT / "nkp-ocr", args.end)
    if not args.pilot and info["missing_printed_pages"]:
        raise ValueError("Full corpus output requires complete expected primary page coverage")
    prefix = "pilot-" if args.pilot else ""
    (ROOT / f"{prefix}hus-postilla-erben-1866.txt").write_text(result, encoding="utf-8")
    (ROOT / f"{prefix}hus-postilla-cleaning.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: val for key, val in info.items() if key != "page_manifest"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
