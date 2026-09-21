import csv
import zipfile

import pytest

from phi_guardrails import fetch


def test_datasets_point_at_cms():
    # Arrange
    datasets = fetch.DATASETS

    # Act
    urls = [ds["url"] for ds in datasets.values()]

    # Assert
    assert set(datasets) == {"beneficiary", "inpatient_claims"}
    assert all(url.startswith("https://www.cms.gov/") for url in urls)


def test_download_skips_existing(tmp_path):
    # Arrange
    dest = tmp_path / "already.zip"
    dest.write_bytes(b"sentinel")

    # Act
    fetch.download("https://example.invalid/nope.zip", dest)

    # Assert
    assert dest.read_bytes() == b"sentinel"


def test_download_writes_stream(tmp_path, monkeypatch):
    # Arrange
    dest = tmp_path / "fresh.zip"

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1):
            yield b"part1"
            yield b"part2"

    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: FakeResp())

    # Act
    fetch.download("https://example.invalid/x.zip", dest)

    # Assert
    assert dest.read_bytes() == b"part1part2"


def test_extract_pulls_single_csv(tmp_path):
    # Arrange
    zip_path = tmp_path / "sample.zip"
    csv_path = tmp_path / "out.csv"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv", "A,B\n1,2\n")

    # Act
    fetch.extract(zip_path, csv_path)

    # Assert
    assert list(csv.reader(csv_path.open())) == [["A", "B"], ["1", "2"]]


def test_extract_rejects_multiple_csvs(tmp_path):
    # Arrange
    zip_path = tmp_path / "multi.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("a.csv", "x\n")
        zf.writestr("b.csv", "y\n")

    # Act / Assert
    with pytest.raises(ValueError, match="exactly one CSV"):
        fetch.extract(zip_path, tmp_path / "out.csv")


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("h1,h2\n", 0),
        ("h1,h2\n1,2\n", 1),
        ("h1,h2\n1,2\n3,4\n", 2),
    ],
)
def test_row_count(tmp_path, content, expected):
    # Arrange
    p = tmp_path / "c.csv"
    p.write_text(content)

    # Act
    n = fetch.row_count(p)

    # Assert
    assert n == expected
