"""Download and extract the CMS SYNPUF sample files into data/.

Usage:
    uv run python -m phi_guardrails.fetch
"""

from __future__ import annotations

import csv
import sys
import zipfile
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

DATASETS = {
    "beneficiary": {
        "url": (
            "https://www.cms.gov/research-statistics-data-and-systems/"
            "downloadable-public-use-files/synpufs/downloads/"
            "de1_0_2008_beneficiary_summary_file_sample_1.zip"
        ),
        "zip": "beneficiary_sample_1.zip",
        "csv": "beneficiary.csv",
    },
    "inpatient_claims": {
        "url": (
            "https://www.cms.gov/research-statistics-data-and-systems/"
            "downloadable-public-use-files/synpufs/downloads/"
            "de1_0_2008_to_2010_inpatient_claims_sample_1.zip"
        ),
        "zip": "inpatient_claims_sample_1.zip",
        "csv": "inpatient_claims.csv",
    },
}


def download(url: str, dest: Path) -> None:
    """Stream a URL to dest, skipping if already present."""
    if dest.exists():
        print(f"  exists: {dest.name} (skipping download)")
        return
    print(f"  downloading {url}")
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with dest.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                f.write(chunk)


def extract(zip_path: Path, csv_path: Path) -> None:
    """Extract the single CSV inside the zip to csv_path."""
    if csv_path.exists():
        print(f"  exists: {csv_path.name} (skipping extraction)")
        return
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        csv_names = [n for n in names if n.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"expected exactly one CSV in {zip_path}, got {names}")
        with zf.open(csv_names[0]) as src, csv_path.open("wb") as dst:
            dst.write(src.read())
    print(f"  extracted: {csv_path.name}")


def row_count(csv_path: Path) -> int:
    with csv_path.open(newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def fetch_all(data_dir: Path = DATA_DIR) -> dict[str, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for name, ds in DATASETS.items():
        print(f"[{name}]")
        zip_path = data_dir / ds["zip"]
        csv_path = data_dir / ds["csv"]
        download(ds["url"], zip_path)
        extract(zip_path, csv_path)
        print(f"  rows: {row_count(csv_path)}")
        out[name] = csv_path
    return out


def main() -> int:
    paths = fetch_all()
    print("\nDone. CSVs in data/:")
    for name, p in paths.items():
        print(f"  {name}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
