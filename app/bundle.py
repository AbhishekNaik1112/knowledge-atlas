"""Read OKF bundle files from a directory or a zip. Shared by ingest and validate."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_ZIP_FILES = 500
MAX_ZIP_UNCOMPRESSED_BYTES = 20 * 1024 * 1024  # 20 MB


@dataclass(frozen=True)
class BundleEntry:
    rel_path: str
    text: str


class BundleReadError(ValueError):
    """Raised when a bundle directory or zip cannot be read or decoded."""


def read_dir(dir_path: str) -> tuple[str, list[BundleEntry]]:
    """Return (bundle_name, entries) for every .md under dir_path. Raises ValueError if not a dir."""
    root = Path(dir_path)
    if not root.is_dir():
        raise BundleReadError(f"not a directory: {dir_path}")
    try:
        entries = [
            BundleEntry(p.relative_to(root).as_posix(), p.read_text(encoding="utf-8"))
            for p in sorted(root.rglob("*.md"))
        ]
    except UnicodeDecodeError as exc:
        raise BundleReadError(f"invalid UTF-8 encoding in bundle: {exc}") from exc
    return root.name, entries


def read_zip(data: bytes) -> list[BundleEntry]:
    entries: list[BundleEntry] = []
    total_bytes = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = [i for i in sorted(zf.infolist(), key=lambda x: x.filename) if not i.is_dir()]
            if len(infos) > MAX_ZIP_FILES:
                raise BundleReadError(f"zip contains too many files (max {MAX_ZIP_FILES})")
            for info in infos:
                name = info.filename
                if name.startswith(("/", "\\")) or ".." in PurePosixPath(name.replace("\\", "/")).parts:
                    raise BundleReadError(f"unsafe zip entry path: {name}")
                total_bytes += info.file_size
                if total_bytes > MAX_ZIP_UNCOMPRESSED_BYTES:
                    raise BundleReadError("zip uncompressed size exceeds limit")
                if not name.lower().endswith(".md"):
                    continue
                raw = zf.read(name)
                if len(raw) > MAX_ZIP_UNCOMPRESSED_BYTES:
                    raise BundleReadError("zip entry size exceeds limit")
                entries.append(BundleEntry(name, raw.decode("utf-8")))
    except (zipfile.BadZipFile, UnicodeDecodeError) as exc:
        raise BundleReadError(f"invalid zip bundle: {exc}") from exc
    return entries
