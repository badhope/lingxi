"""File validation for the knowledge-base upload endpoint.

Returns (ok, error_message) tuples and a safe filename helper. The set of
allowed extensions and size cap are intentionally small — the KB does
keyword search, so binary uploads don't make sense.
"""
from __future__ import annotations

import os
import re
from typing import Tuple

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".log", ".py"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file(filename: str, size: int) -> Tuple[bool, str]:
    """Check extension and size. Returns (ok, error_msg)."""
    if not filename:
        return False, "filename is required"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"unsupported extension {ext!r}"
    if size > MAX_FILE_SIZE:
        return False, f"file too large ({size} > {MAX_FILE_SIZE})"
    return True, ""


_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters from a filename."""
    base = os.path.basename(filename or "")
    base = _SAFE.sub("_", base).strip("._")
    return base or "upload"


__all__ = ["validate_file", "sanitize_filename", "ALLOWED_EXTENSIONS", "MAX_FILE_SIZE"]
