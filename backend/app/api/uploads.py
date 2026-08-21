"""Upload and manage secondary-data files attached to a project.

Brand teams hold data no public source carries — IQVIA/AWACS extracts, internal
price lists, market research decks. This lets those files sit alongside the
fetched data instead of living in someone's inbox.

Upload handling is the classic path for directory traversal and content
smuggling, so filenames are regenerated rather than trusted, extensions are
allow-listed, and size is capped while streaming rather than after.
"""
import logging
import os
import re
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uploads", tags=["Secondary Data Uploads"])

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")

# Formats a brand team actually shares. Executables and archives are excluded:
# nothing here needs to run, and an archive hides its contents from this check.
ALLOWED_EXTENSIONS = {
    ".csv", ".tsv", ".xlsx", ".xls", ".pdf", ".docx", ".doc",
    ".pptx", ".ppt", ".txt", ".json", ".png", ".jpg", ".jpeg",
}
# Real secondary-data files are large: an IMS/PharmaTrac base extract runs to
# a few hundred MB. The body is streamed to disk in chunks, so the cap bounds
# disk use rather than memory, and it stays configurable per deployment.
MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "300")) * 1024 * 1024
CHUNK = 4 * 1024 * 1024

_SAFE_PROJECT = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class UploadedFile(BaseModel):
    id: str
    project_id: str
    original_filename: str
    stored_filename: str
    size_bytes: int
    content_type: Optional[str] = None
    uploaded_at: str
    note: Optional[str] = None


def _project_dir(project_id: str) -> str:
    """Resolve a project's upload directory, rejecting traversal attempts."""
    if not _SAFE_PROJECT.match(project_id or ""):
        raise HTTPException(status_code=400, detail="Invalid project id.")
    path = os.path.join(UPLOAD_ROOT, project_id)
    # Belt and braces: confirm the resolved path stays inside the upload root.
    root = os.path.realpath(UPLOAD_ROOT)
    resolved = os.path.realpath(path)
    if not (resolved == root or resolved.startswith(root + os.sep)):
        raise HTTPException(status_code=400, detail="Invalid project id.")
    os.makedirs(resolved, exist_ok=True)
    return resolved


def _safe_original_name(name: str) -> str:
    """Keep a readable label without letting the client choose a path."""
    base = os.path.basename(name or "upload")
    base = re.sub(r"[^\w\s.\-()]", "_", base).strip() or "upload"
    return base[:120]


def _meta_path(directory: str, file_id: str) -> str:
    return os.path.join(directory, f"{file_id}.meta.json")


@router.post("", response_model=UploadedFile)
async def upload_secondary_data(
    project_id: str = Form(..., description="Project the file belongs to"),
    note: Optional[str] = Form(None, description="What this file contains"),
    file: UploadFile = File(...),
):
    """Store one secondary-data file against a project."""
    import json

    directory = _project_dir(project_id)
    original = _safe_original_name(file.filename or "upload")
    extension = os.path.splitext(original)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"'{extension or 'no extension'}' is not an accepted format. "
                   f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_id = uuid.uuid4().hex
    stored = f"{file_id}{extension}"          # never the client's filename
    destination = os.path.join(directory, stored)

    written = 0
    try:
        with open(destination, "wb") as handle:
            while True:
                chunk = await file.read(CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                # Enforce the cap while streaming; a Content-Length header is
                # attacker-controlled and cannot be trusted.
                if written > MAX_BYTES:
                    handle.close()
                    os.remove(destination)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {MAX_BYTES // (1024 * 1024)} MB limit.",
                    )
                handle.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        if os.path.exists(destination):
            os.remove(destination)
        logger.exception("Upload failed for project %s", project_id)
        raise HTTPException(status_code=500, detail="Could not store the file.") from exc

    record = UploadedFile(
        id=file_id,
        project_id=project_id,
        original_filename=original,
        stored_filename=stored,
        size_bytes=written,
        content_type=file.content_type,
        uploaded_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        note=(note or "").strip()[:500] or None,
    )
    with open(_meta_path(directory, file_id), "w") as handle:
        json.dump(record.model_dump(), handle)

    logger.info("Stored %s (%d bytes) for project %s", original, written, project_id)
    return record


@router.get("/{project_id}", response_model=List[UploadedFile])
async def list_secondary_data(project_id: str):
    """Every file attached to a project."""
    import json

    directory = _project_dir(project_id)
    records: List[UploadedFile] = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".meta.json"):
            continue
        try:
            with open(os.path.join(directory, name)) as handle:
                records.append(UploadedFile(**json.load(handle)))
        except Exception:
            logger.warning("Skipping unreadable upload metadata: %s", name)
    records.sort(key=lambda r: r.uploaded_at, reverse=True)
    return records


@router.get("/{project_id}/{file_id}/download")
async def download_secondary_data(project_id: str, file_id: str):
    """Return a stored file by id."""
    import json

    if not re.fullmatch(r"[0-9a-f]{32}", file_id or ""):
        raise HTTPException(status_code=400, detail="Invalid file id.")
    directory = _project_dir(project_id)
    meta = _meta_path(directory, file_id)
    if not os.path.exists(meta):
        raise HTTPException(status_code=404, detail="File not found.")
    with open(meta) as handle:
        record = UploadedFile(**json.load(handle))
    path = os.path.join(directory, record.stored_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(
        path,
        media_type=record.content_type or "application/octet-stream",
        filename=record.original_filename,
    )


@router.delete("/{project_id}/{file_id}")
async def delete_secondary_data(project_id: str, file_id: str):
    if not re.fullmatch(r"[0-9a-f]{32}", file_id or ""):
        raise HTTPException(status_code=400, detail="Invalid file id.")
    directory = _project_dir(project_id)
    meta = _meta_path(directory, file_id)
    if not os.path.exists(meta):
        raise HTTPException(status_code=404, detail="File not found.")

    import json
    with open(meta) as handle:
        record = UploadedFile(**json.load(handle))
    for path in (os.path.join(directory, record.stored_filename), meta):
        if os.path.exists(path):
            os.remove(path)
    return {"deleted": file_id}
