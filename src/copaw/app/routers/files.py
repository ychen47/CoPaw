# -*- coding: utf-8 -*-
"""File upload API – accept multipart uploads and serve them back."""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ...constant import WORKING_DIR

router = APIRouter(prefix="/files", tags=["files"])

# Uploads are stored under WORKING_DIR/uploads
_UPLOAD_DIR = WORKING_DIR / "uploads"

_MAX_FILENAME_LEN = 255
_ALLOWED_CHARS = re.compile(r"[^\w\-. ]")


def _safe_filename(name: str) -> str:
    """Sanitize an upload filename to prevent path traversal."""
    # Keep only the final component, strip directory separators
    name = Path(name).name
    # Replace disallowed characters with underscores
    name = _ALLOWED_CHARS.sub("_", name)
    # Truncate
    return name[:_MAX_FILENAME_LEN] or "upload"


def _unique_path(directory: Path, filename: str) -> Path:
    """Return a path under *directory* that does not yet exist."""
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = directory / filename
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


@router.post("/upload")
async def upload_file(file: UploadFile):
    """Accept a single file upload and return its server-side URL.

    The response body has the shape expected by antd's ``customRequest``
    ``onSuccess`` callback::

        { "url": "/api/files/serve/<filename>", "name": "<filename>" }
    """
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_filename(file.filename or "upload")
    dest = _unique_path(_UPLOAD_DIR, safe_name)

    # Resolve and guard against any residual traversal
    if not dest.resolve().is_relative_to(_UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    content = await file.read()
    dest.write_bytes(content)

    # Return a file:// URI so the agent can resolve the upload to a local path.
    # The /api/files/serve/ endpoint is still available for browser previews.
    return {"url": dest.resolve().as_uri(), "name": dest.name}


@router.get("/serve/{filename}")
async def serve_file(filename: str):
    """Serve a previously uploaded file."""
    safe_name = _safe_filename(filename)
    path = (_UPLOAD_DIR / safe_name).resolve()

    if not path.is_relative_to(_UPLOAD_DIR.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    media_type, _ = mimetypes.guess_type(str(path))
    return FileResponse(path, media_type=media_type or "application/octet-stream")
