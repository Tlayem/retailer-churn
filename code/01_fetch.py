#!/usr/bin/env python3
"""01_fetch.py — obtain the two raw inputs and log provenance.

Inputs (both U.S. government works, public domain):
  1. USDA FNS, SNAP Retailer Locator Historical Data 2005-2025
     (current as of 31 Dec 2025; page updated 19 Feb 2026)
  2. USDA ERS, Food Access Research Atlas, 2025 SNAP-authorized Retailer
     Access Map (SRAM) data (initial release July 2026; updated 27 Jul 2026)

The script tries to download each file. USDA hosts block some automated
clients; if the download fails, save the file by hand from the landing page
into data/raw/ under the name below and re-run. Either way the script records
bytes and SHA-256 in data/raw/PROVENANCE.txt and extracts the archive.

Usage:  python code/01_fetch.py
"""
import datetime
import hashlib
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LOG = RAW / "PROVENANCE.txt"

SOURCES = [
    dict(
        name="snap-retailer-locator-data2005-2025.zip",
        url="https://www.fna.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip",
        landing="https://www.fna.usda.gov/snap/retailer-locator/data",
        expect_sha="872a6f814a63514a1f1b0c4517a90309a9fbb01d97d6e4dbb1e8b20421c08cce",
    ),
    dict(
        name="2025-sram-fara-data.zip",
        url="https://www.ers.usda.gov/media/29395/2025-snap-authorized-retailer-access-map-sram-data.zip?v=85613",
        landing="https://www.ers.usda.gov/data-products/food-access-research-atlas/download-the-data",
        expect_sha="8e8ccda55aa478dd5907050249c28157d445568d242db8b5f85231b82c8afdbf",
    ),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for s in SOURCES:
        dest = RAW / s["name"]
        how = "already present (browser download by author)"
        if not dest.exists():
            try:
                req = urllib.request.Request(s["url"], headers={"User-Agent": "Mozilla/5.0 (compatible; research replication)"})
                with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                    f.write(r.read())
                how = "downloaded by 01_fetch.py"
            except Exception as e:  # noqa: BLE001
                raise SystemExit(
                    f"Could not download {s['name']} ({e}).\n"
                    f"Download it by hand from {s['landing']} and save it as {dest}, then re-run."
                )
        digest = sha256(dest)
        match = "matches" if digest == s["expect_sha"] else "DIFFERS FROM"
        line = " | ".join([
            datetime.date.today().isoformat(), s["name"], f"{dest.stat().st_size} bytes",
            f"sha256:{digest}", s["url"], f"{how}; {match} the hash used for the paper",
        ])
        existing = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
        if f"sha256:{digest}" not in existing:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        print(line)
        if match != "matches":
            print("  WARNING: this is a different vintage from the one the paper was built on; numbers will differ.")
        with zipfile.ZipFile(dest) as z:
            z.extractall(RAW / "extracted")


if __name__ == "__main__":
    main()
