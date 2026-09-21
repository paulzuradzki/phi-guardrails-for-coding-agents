import csv
import zipfile

from phi_guardrails import fetch


def test_datasets_point_at_cms():
    for name, ds in fetch.DATASETS.items():
        assert ds["url"].startswith("https://www.cms.gov/")
        assert ds["zip"].endswith(".zip")
        assert ds["csv"].endswith(".csv")
        assert name in ("beneficiary", "inpatient_claims")


def test_download_skips_existing(tmp_path):
    dest = tmp_path / "already.zip"
    dest.write_bytes(b"sentinel")
    fetch.download("https://example.invalid/nope.zip", dest)
    assert dest.read_bytes() == b"sentinel"


def test_download_writes_stream(tmp_path, monkeypatch):
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
    fetch.download("https://example.invalid/x.zip", dest)
    assert dest.read_bytes() == b"part1part2"


def test_extract_pulls_single_csv(tmp_path):
    zip_path = tmp_path / "sample.zip"
    csv_path = tmp_path / "out.csv"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv", "A,B\n1,2\n")
    fetch.extract(zip_path, csv_path)
    assert list(csv.reader(csv_path.open())) == [["A", "B"], ["1", "2"]]


def test_extract_rejects_multiple_csvs(tmp_path):
    zip_path = tmp_path / "multi.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("a.csv", "x\n")
        zf.writestr("b.csv", "y\n")
    try:
        fetch.extract(zip_path, tmp_path / "out.csv")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "exactly one CSV" in str(e)


def test_row_count(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text("h1,h2\n1,2\n3,4\n")
    assert fetch.row_count(p) == 2
