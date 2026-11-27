"""Fetch published OCR for the double-checked 434 numbered NDK pages."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from threading import Lock
from time import monotonic, sleep


ROOT = Path(__file__).resolve().parent
PAGES = ROOT / "source-audit" / "erben-nkp-page-index.json"
RAW = ROOT / "nkp-ocr"
URL = "https://kramerius5.nkp.cz/search/api/v5.0/item/{pid}/streams/TEXT_OCR"
DOWNLOAD_DELAY = 0.5


def roster():
    objects = json.loads(PAGES.read_text())["response"]["docs"]
    rows = []
    for row in objects:
        label = row["page.number"].strip("[]")
        if not re.fullmatch(r"[0-9]+", label) or not 1 <= int(label) <= 434:
            continue
        if row["accessibility"] != "public" or row.get("licenses.facet") != ["public"]:
            raise ValueError(f"Public status missing for {label}")
        rows.append((int(label), row["pid"]))
    rows.sort()
    if [number for number, _ in rows] != list(range(1, 435)):
        raise ValueError("Expected each printed page 1 to 434 exactly once")
    return rows


def decode(raw):
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8-sig")
    if "\ufffd" in text or "\x00" in text or len(text.strip()) < 15:
        raise ValueError("Malformed or missing OCR")
    if text.lstrip().startswith(("<html", "<!DOCTYPE", "<?xml")):
        raise ValueError("Server returned markup instead of page OCR")
    return text


class Throttle:
    def __init__(self):
        self.next_start = 0
        self.lock = Lock()

    def start(self):
        with self.lock:
            sleep(max(0, self.next_start - monotonic()))
            self.next_start = monotonic() + DOWNLOAD_DELAY


def fetch(page, pid, throttle):
    path = RAW / f"{page:03}.txt"
    if path.exists():
        raw = path.read_bytes()
    else:
        throttle.start()
        result = subprocess.run(
            ["curl", "-fsSL", "--max-time", "15", "--retry", "1",
             "--user-agent", "VoynichSwarm-research/1.0 (public library OCR audit)",
             URL.format(pid=pid)],
            capture_output=True,
            check=True,
        )
        raw = result.stdout
        decode(raw)
        path.write_bytes(raw)
    parsed = decode(raw)
    return {"page": page, "pid": pid, "sha256": sha256(raw).hexdigest(),
            "bytes": len(raw), "decoded_chars": len(parsed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end", type=int, default=434)
    args = parser.parse_args()
    rows = [row for row in roster() if row[0] <= args.end]
    RAW.mkdir(exist_ok=True)
    throttle = Throttle()
    succeeded, errors = [], []
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = {executor.submit(fetch, page, pid, throttle): (page, pid) for page, pid in rows}
        for job in as_completed(jobs):
            try:
                succeeded.append(job.result())
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                page, pid = jobs[job]
                errors.append({"page": page, "pid": pid, "error": str(error)})
            complete = len(succeeded) + len(errors)
            if complete % 35 == 0 or complete == len(jobs):
                print(f"{complete}/{len(jobs)} checked, {len(errors)} errors", flush=True)
    result = {"volume_uuid": "3a69fd10-04b1-11dd-abf7-000d606f5dc6", "source": URL,
              "pages": sorted(succeeded, key=lambda row: row["page"]),
              "errors": sorted(errors, key=lambda row: row["page"])}
    (ROOT / "nkp-ocr-manifest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
