import os
import re
import uuid
import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from supabase import create_client, Client
from app.config import get_settings
from app.db import execute_query
from app.auth import get_current_user
from app.rag.extract import parse_document
from app.rag.chunk import chunk_text
from app.rag.embed import embed_texts

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/documents", tags=["Documents"])

def sanitize_filename(name: str) -> str:
    """
    Sanitizes file names to prevent path traversal and arbitrary injection.
    Extracts base name and keeps only alphanumeric characters, dots, underscores, and hyphens.
    """
    base = os.path.basename(name).strip()
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', base)
    return safe[:100] if safe else "document"

def validate_file_magic_bytes(file_bytes: bytes, ext: str):
    """
    Validates magic byte signatures to prevent MIME-type / extension spoofing.
    """
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "empty_file", "message": "Uploaded file is empty (0 bytes)."}
        )
    if ext == "pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_magic_bytes", "message": "File content does not match a valid PDF header (%PDF-)."}
            )
    elif ext == "docx":
        if not file_bytes.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_magic_bytes", "message": "File content does not match a valid DOCX zip container (PK..)."}
            )
    elif ext == "txt":
        # Disallow executable headers renamed as .txt
        if file_bytes.startswith(b"MZ") or file_bytes.startswith(b"\x7fELF") or file_bytes.startswith(b"\xca\xfe\xba\xbe"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "executable_prohibited", "message": "Executable binary files are strictly prohibited."}
            )

def get_supabase_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)

def process_document_background(document_id: str, user_id: str, file_bytes: bytes, filename: str):
    """
    Background worker that extracts text, chunks it, generates embeddings,
    and inserts chunks into the pgvector table. Updates document status.
    """
    try:
        # 1. Parse text
        full_text, _ = parse_document(file_bytes, filename)

        # 2. Chunk text
        chunks = chunk_text(full_text)
        if not chunks:
            raise ValueError("No valid passages generated from document.")

        # 3. Embed chunks in batches
        embeddings = embed_texts(chunks, batch_size=32)

        # 4. Insert chunks into database
        with get_db_cursor() as cur:
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                emb_str = f"[{','.join(map(str, emb))}]"
                cur.execute(
                    """
                    INSERT INTO chunks (document_id, user_id, chunk_index, text, embedding)
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s::vector)
                    """,
                    (document_id, user_id, idx + 1, chunk, emb_str)
                )

            # Update document to ready
            cur.execute(
                """
                UPDATE documents 
                SET status = 'ready', error = NULL 
                WHERE id = %s::uuid
                """,
                (document_id,)
            )
            logger.info(f"Document {document_id} processed successfully with {len(chunks)} chunks.")

    except Exception as e:
        logger.error(f"Failed processing document {document_id}: {e}")
        error_msg = str(e)
        if "No readable text found" in error_msg:
            user_error = "No readable text found. Upload a text-based PDF, not a scan."
        else:
            user_error = f"Processing error: {error_msg}"

        execute_query(
            "UPDATE documents SET status = 'failed', error = %s WHERE id = %s::uuid",
            (user_error, document_id)
        )

from app.db import get_db
from contextlib import contextmanager

@contextmanager
def get_db_cursor():
    with get_db() as conn:
        with conn.cursor() as cur:
            yield cur

@router.get("")
async def list_documents(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    query = """
    SELECT 
        d.id,
        d.name,
        d.type,
        d.size_bytes,
        d.uploaded_at,
        d.status,
        d.error,
        COUNT(c.id) as passages
    FROM documents d
    LEFT JOIN chunks c ON c.document_id = d.id
    WHERE d.user_id = %s::uuid
    GROUP BY d.id
    ORDER BY d.uploaded_at DESC;
    """
    rows = execute_query(query, (user_id,), fetch_all=True)
    results = []
    for r in rows:
        results.append({
            "id": str(r["id"]),
            "name": r["name"],
            "type": r["type"],
            "size_bytes": r["size_bytes"],
            "uploaded_at": r["uploaded_at"].isoformat() if r["uploaded_at"] else None,
            "status": r["status"],
            "passages": r["passages"],
            "error": r["error"]
        })
    return results

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    raw_filename = file.filename or "uploaded_file"
    filename = sanitize_filename(raw_filename)
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext not in ["pdf", "docx", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "unsupported_type", "message": "Only PDF, DOCX, and TXT files are supported."}
        )

    file_bytes = await file.read()
    size_bytes = len(file_bytes)

    # Magic byte validation to prevent spoofing
    validate_file_magic_bytes(file_bytes, ext)

    # 10 MB limit check
    if size_bytes > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "file_too_large", "message": "File exceeds the 10 MB size limit."}
        )

    doc_id = str(uuid.uuid4())
    doc_type = ext.upper()
    storage_path = f"{user_id}/{doc_id}_{filename}"

    # Upload raw file to Supabase Storage
    try:
        supabase = get_supabase_client()
        supabase.storage.from_(settings.supabase_storage_bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )
    except Exception as e:
        logger.warning(f"Storage upload notice: {e}")

    # Insert document record with 'processing' status
    doc_row = execute_query(
        """
        INSERT INTO documents (id, user_id, name, type, size_bytes, storage_path, status, error, uploaded_at)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, 'processing', NULL, now())
        RETURNING id, name, type, size_bytes, uploaded_at, status
        """,
        (doc_id, user_id, filename, doc_type, size_bytes, storage_path),
        fetch_one=True
    )

    # Queue background task for text extraction, chunking, and embedding
    background_tasks.add_task(
        process_document_background,
        doc_id,
        user_id,
        file_bytes,
        filename
    )

    return {
        "id": str(doc_row["id"]),
        "name": doc_row["name"],
        "type": doc_row["type"],
        "size_bytes": doc_row["size_bytes"],
        "uploaded_at": doc_row["uploaded_at"].isoformat(),
        "status": doc_row["status"],
        "passages": 0,
        "error": None
    }

class TextDocumentRequest(BaseModel):
    name: str
    text: str

@router.post("/text", status_code=status.HTTP_202_ACCEPTED)
async def create_text_document(
    req: TextDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    name = req.name.strip() or "Untitled Document"
    file_bytes = req.text.encode("utf-8")
    size_bytes = len(file_bytes)
    doc_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{doc_id}_{name}.txt"

    doc_row = execute_query(
        """
        INSERT INTO documents (id, user_id, name, type, size_bytes, storage_path, status, error, uploaded_at)
        VALUES (%s::uuid, %s::uuid, %s, 'TXT', %s, %s, 'processing', NULL, now())
        RETURNING id, name, type, size_bytes, uploaded_at, status
        """,
        (doc_id, user_id, name, size_bytes, storage_path),
        fetch_one=True
    )

    background_tasks.add_task(
        process_document_background,
        doc_id,
        user_id,
        file_bytes,
        f"{name}.txt"
    )

    return {
        "id": str(doc_row["id"]),
        "name": doc_row["name"],
        "type": doc_row["type"],
        "size_bytes": doc_row["size_bytes"],
        "uploaded_at": doc_row["uploaded_at"].isoformat(),
        "status": doc_row["status"],
        "passages": 0,
        "error": None
    }

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    doc = execute_query(
        "SELECT id, storage_path FROM documents WHERE id = %s::uuid AND user_id = %s::uuid",
        (document_id, user_id),
        fetch_one=True
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Document not found or belongs to another user."}
        )

    # Delete from Supabase Storage
    try:
        if doc.get("storage_path"):
            supabase = get_supabase_client()
            supabase.storage.from_(settings.supabase_storage_bucket).remove([doc["storage_path"]])
    except Exception as e:
        logger.warning(f"Storage delete notice: {e}")

    # Delete from DB (on delete cascade automatically removes related chunks)
    execute_query("DELETE FROM documents WHERE id = %s::uuid", (document_id,))
    return None

@router.get("/{document_id}/download")
async def get_document_download_url(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generates a secure, short-lived signed download URL (15 minutes expiration).
    Strictly enforces document ownership.
    """
    user_id = current_user["id"]
    doc = execute_query(
        "SELECT id, name, storage_path FROM documents WHERE id = %s::uuid AND user_id = %s::uuid",
        (document_id, user_id),
        fetch_one=True
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Document not found or belongs to another user."}
        )

    storage_path = doc.get("storage_path")
    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "file_not_in_storage", "message": "Document binary file not found in storage."}
        )

    try:
        supabase = get_supabase_client()
        # 900 seconds = 15 minutes signed URL expiration
        signed_res = supabase.storage.from_(settings.supabase_storage_bucket).create_signed_url(storage_path, 900)
        signed_url = signed_res.get("signedURL") or signed_res.get("signedUrl")
        return {
            "document_id": document_id,
            "filename": doc["name"],
            "download_url": signed_url,
            "expires_in_seconds": 900
        }
    except Exception as e:
        logger.error(f"Error generating signed URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "storage_error", "message": "Failed to generate signed download link."}
        )
