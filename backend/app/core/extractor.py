import os
import shutil
import zipfile
from pathlib import Path
from typing import Tuple, List
from app.core.config import settings


class ArchiveSecurityError(Exception):
    """Raised when an uploaded archive violates security boundaries or limits."""
    pass


def is_safe_path(target_dir: Path, target_path: Path) -> bool:
    """Verify that the resolved path is inside target_dir to prevent Zip Slip."""
    try:
        resolved_target = target_path.resolve()
        resolved_base = target_dir.resolve()
        return resolved_base in resolved_target.parents or resolved_target == resolved_base
    except Exception:
        return False


def validate_and_extract_zip(zip_path: Path, extract_to: Path) -> Tuple[int, int]:
    """
    Safely validates and extracts a ZIP archive.
    
    Protects against:
    - Zip Slip (path traversal / outside directory writes)
    - Zip Bombs (decompression amplification & memory exhaustion)
    - Exceeding file counts or size limits
    - Symlinks and dangerous file descriptors
    
    Returns:
        (files_extracted_count, total_uncompressed_bytes)
    """
    if not zipfile.is_zipfile(zip_path):
        raise ArchiveSecurityError("Uploaded file is not a valid ZIP archive.")

    extract_to.mkdir(parents=True, exist_ok=True)
    total_uncompressed_bytes = 0
    file_count = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        infolist = zf.infolist()

        if len(infolist) > settings.max_file_count:
            raise ArchiveSecurityError(
                f"Archive contains {len(infolist)} entries, exceeding the maximum allowed limit of {settings.max_file_count}."
            )

        # Preliminary check on declared uncompressed size
        declared_total_size = sum(info.file_size for info in infolist)
        if declared_total_size > settings.max_extracted_size_bytes:
            raise ArchiveSecurityError(
                f"Archive declared uncompressed size ({declared_total_size} bytes) exceeds limit of {settings.max_extracted_size_bytes} bytes."
            )

        for member in infolist:
            filename = member.filename

            # Reject empty names or absolute paths
            if not filename or filename.startswith("/") or filename.startswith("\\"):
                raise ArchiveSecurityError(f"Malicious archive member detected: {filename}")

            # Check destination path safely
            target_file_path = extract_to / filename
            if not is_safe_path(extract_to, target_file_path):
                raise ArchiveSecurityError(f"Zip Slip path traversal attempt detected in entry: {filename}")

            # Prevent symlinks: mode 0o120000 in UNIX indicates a symlink
            unix_mode = member.external_attr >> 16
            if unix_mode & 0o120000 == 0o120000:
                # Disallow symlinks to prevent reading arbitrary server files
                continue

            # Skip directory entries
            if member.is_dir():
                target_file_path.mkdir(parents=True, exist_ok=True)
                continue

            # Compression ratio check per file (defense against zip bombs)
            if member.compress_size > 0:
                ratio = member.file_size / member.compress_size
                if ratio > settings.max_compression_ratio:
                    raise ArchiveSecurityError(
                        f"Excessive compression ratio ({ratio:.1f}) in {filename}. Possible zip bomb."
                    )

            # Ensure parent directories exist
            target_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract with streaming chunk size enforcement
            bytes_read_this_file = 0
            with zf.open(member) as source, open(target_file_path, "wb") as target:
                while True:
                    chunk = source.read(64 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
                    bytes_read_this_file += len(chunk)
                    total_uncompressed_bytes += len(chunk)

                    if total_uncompressed_bytes > settings.max_extracted_size_bytes:
                        raise ArchiveSecurityError(
                            f"Extracted data exceeded maximum limit of {settings.max_extracted_size_bytes} bytes."
                        )

            file_count += 1

    return file_count, total_uncompressed_bytes


def cleanup_directory(directory_path: Path) -> None:
    """Safely cleans up an extracted temporary directory."""
    if directory_path.exists() and directory_path.is_dir():
        try:
            shutil.rmtree(directory_path, ignore_errors=True)
        except Exception:
            pass
