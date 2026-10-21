import io
import zipfile
import pytest
from pathlib import Path
from app.core.extractor import validate_and_extract_zip, ArchiveSecurityError


def test_safe_zip_extraction(tmp_path: Path):
    # Create a safe zip file
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("test.py", "print('hello world')")
        zf.writestr("subfolder/utils.py", "def add(a, b): return a + b")

    zip_file = tmp_path / "valid.zip"
    zip_file.write_bytes(zip_bytes.getvalue())

    dest_dir = tmp_path / "extracted"
    file_count, total_bytes = validate_and_extract_zip(zip_file, dest_dir)

    assert file_count == 2
    assert (dest_dir / "test.py").exists()
    assert (dest_dir / "subfolder" / "utils.py").exists()
    assert (dest_dir / "test.py").read_text() == "print('hello world')"


def test_reject_zip_slip_path_traversal(tmp_path: Path):
    # Create a malicious zip file attempting Zip Slip
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("../../evil.sh", "echo pwned")

    bad_zip = tmp_path / "malicious.zip"
    bad_zip.write_bytes(zip_bytes.getvalue())

    dest_dir = tmp_path / "extracted"
    with pytest.raises(ArchiveSecurityError) as exc_info:
        validate_and_extract_zip(bad_zip, dest_dir)

    assert "Zip Slip" in str(exc_info.value) or "Malicious" in str(exc_info.value)


def test_reject_invalid_zip(tmp_path: Path):
    not_a_zip = tmp_path / "fake.zip"
    not_a_zip.write_text("This is not a zip file content.")

    dest_dir = tmp_path / "extracted"
    with pytest.raises(ArchiveSecurityError):
        validate_and_extract_zip(not_a_zip, dest_dir)
