"""Document upload and management endpoints."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_current_user
from app.config import get_settings
from app.database.supabase_client import (
    delete_document,
    delete_file_from_storage,
    get_chunks_by_document,
    get_document,
    insert_chunks,
    insert_document,
    list_documents,
    update_document,
    upload_file_to_storage,
)
from app.embeddings.embedder import embed_texts
from app.ingestion.document_parser import (
    ParseError,
    UnsupportedFormatError,
    parse_document,
)
from app.preprocessing.chunker import chunk_document
from app.vectorstore.faiss_store import get_faiss_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload and index a document.

    Pipeline: parse → chunk → embed → FAISS index → store metadata.
    """
    settings = get_settings()
    user_id = user["id"]

    # Validate file size
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=422,
            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum "
            f"({settings.max_file_size_mb}MB)",
        )

    # Validate file type
    filename = file.filename or "unnamed"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx", "txt"):
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {ext}. Allowed: pdf, docx, txt",
        )

    doc_id = str(uuid4())

    # Insert initial document record
    doc_record = insert_document(
        {
            "id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "file_type": ext,
            "file_size_bytes": len(file_bytes),
            "status": "processing",
        }
    )

    try:
        # Layer 1: Parse
        document = parse_document(filename, file_bytes, ext)
        document.document_id = doc_id  # Use consistent ID

        # Layer 2: Chunk
        chunks = chunk_document(document)

        if not chunks:
            update_document(doc_id, {
                "status": "failed",
                "error_message": "No text content extracted from document",
            })
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in document",
            )

        # Layer 3: Embed
        chunk_texts = [c.text for c in chunks]
        embeddings = embed_texts(chunk_texts)

        # Layer 4: FAISS index
        faiss_store = get_faiss_store()
        chunk_id_strings = [str(c.chunk_id) for c in chunks]
        faiss_store.add_chunks(chunk_id_strings, embeddings)
        faiss_store.save()

        # Store chunks in Supabase
        chunk_records = [
            {
                "id": str(c.chunk_id),
                "document_id": doc_id,
                "chunk_index": c.chunk_index,
                "text": c.text,
                "token_count": c.token_count,
                "page_number": c.page_number,
            }
            for c in chunks
        ]
        insert_chunks(chunk_records)

        # Upload original file to storage
        content_type = file.content_type or "application/octet-stream"
        storage_path = upload_file_to_storage(
            user_id, doc_id, filename, file_bytes, content_type
        )

        # Update document status
        update_document(
            doc_id,
            {
                "status": "indexed",
                "total_pages": document.total_pages,
                "chunk_count": len(chunks),
                "storage_path": storage_path,
            },
        )

        logger.info(
            f"Document '{filename}' indexed: {len(chunks)} chunks, "
            f"user={user_id}"
        )

        return {
            "data": {
                "document_id": doc_id,
                "filename": filename,
                "chunk_count": len(chunks),
                "total_pages": document.total_pages,
                "status": "indexed",
            },
            "error": None,
        }

    except (UnsupportedFormatError, ParseError) as e:
        update_document(
            doc_id, {"status": "failed", "error_message": str(e)}
        )
        status_code = 422 if isinstance(e, UnsupportedFormatError) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed for '{filename}': {e}")
        update_document(
            doc_id, {"status": "failed", "error_message": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get("/documents")
async def get_documents(user: dict = Depends(get_current_user)):
    """List all documents for the current user."""
    docs = list_documents(user["id"])
    return {"data": docs, "error": None}


@router.delete("/document/{document_id}")
async def remove_document(
    document_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a document and its associated chunks and vectors."""
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunk IDs for FAISS removal
    chunks = get_chunks_by_document(document_id)
    chunk_ids = [c["id"] for c in chunks]

    # Remove from FAISS
    faiss_store = get_faiss_store()
    faiss_store.delete_by_document_id(chunk_ids)
    faiss_store.save()

    # Delete from storage
    if doc.get("storage_path"):
        try:
            delete_file_from_storage(doc["storage_path"])
        except Exception as e:
            logger.warning(f"Failed to delete storage file: {e}")

    # Delete from Supabase (chunks cascade)
    delete_document(document_id)

    logger.info(f"Document '{document_id}' deleted")
    return {"data": {"deleted": True}, "error": None}
