"""Supabase client singleton for database and storage operations.

Provides async-compatible operations for documents, chunks, queries,
and evaluations tables. Also handles Supabase Storage file uploads.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client, create_client

from app.config import get_settings


_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return singleton Supabase client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _client


# ─── Documents ────────────────────────────────────────────────

def insert_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new document record."""
    client = get_supabase_client()
    result = client.table("documents").insert(data).execute()
    return result.data[0] if result.data else {}


def update_document(doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a document record by ID."""
    client = get_supabase_client()
    result = client.table("documents").update(data).eq("id", doc_id).execute()
    return result.data[0] if result.data else {}


def get_document(doc_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single document by ID."""
    client = get_supabase_client()
    result = client.table("documents").select("*").eq("id", doc_id).execute()
    return result.data[0] if result.data else None


def list_documents(user_id: str) -> List[Dict[str, Any]]:
    """List all documents for a user."""
    client = get_supabase_client()
    result = (
        client.table("documents")
        .select("*")
        .eq("user_id", user_id)
        .order("uploaded_at", desc=True)
        .execute()
    )
    return result.data or []


def delete_document(doc_id: str) -> bool:
    """Delete a document and its chunks (cascaded via FK)."""
    client = get_supabase_client()
    client.table("documents").delete().eq("id", doc_id).execute()
    return True


# ─── Chunks ───────────────────────────────────────────────────

def insert_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Batch insert chunks for a document."""
    client = get_supabase_client()
    result = client.table("chunks").insert(chunks).execute()
    return result.data or []


def get_chunks_by_document(doc_id: str) -> List[Dict[str, Any]]:
    """Fetch all chunks for a document."""
    client = get_supabase_client()
    result = (
        client.table("chunks")
        .select("*")
        .eq("document_id", doc_id)
        .order("chunk_index")
        .execute()
    )
    return result.data or []


def get_chunks_by_ids(chunk_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch chunks by a list of chunk IDs."""
    client = get_supabase_client()
    result = (
        client.table("chunks")
        .select("*, documents(filename)")
        .in_("id", chunk_ids)
        .execute()
    )
    return result.data or []


def get_all_chunks(user_id: str) -> List[Dict[str, Any]]:
    """Fetch all chunks for a user (for BM25 index)."""
    client = get_supabase_client()
    result = (
        client.table("chunks")
        .select("id, text, document_id, page_number, chunk_index")
        .execute()
    )
    return result.data or []


# ─── Queries ──────────────────────────────────────────────────

def insert_query(data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a query log record."""
    client = get_supabase_client()
    result = client.table("queries").insert(data).execute()
    return result.data[0] if result.data else {}


def get_queries(
    user_id: str, limit: int = 50, offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch queries for a user with pagination."""
    client = get_supabase_client()
    result = (
        client.table("queries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data or []


# ─── Evaluations ──────────────────────────────────────────────

def insert_evaluation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert an evaluation result."""
    client = get_supabase_client()
    result = client.table("evaluations").insert(data).execute()
    return result.data[0] if result.data else {}


def get_evaluations(
    user_id: str, limit: int = 50, offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch evaluations for a user (joins through queries)."""
    client = get_supabase_client()
    result = (
        client.table("evaluations")
        .select("*, queries!inner(user_id, query_text)")
        .eq("queries.user_id", user_id)
        .order("evaluated_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data or []


# ─── Storage ─────────────────────────────────────────────────

def upload_file_to_storage(
    user_id: str, doc_id: str, filename: str, file_bytes: bytes, content_type: str
) -> str:
    """Upload a file to Supabase Storage and return the storage path."""
    client = get_supabase_client()
    path = f"{user_id}/{doc_id}/{filename}"
    client.storage.from_("documents").upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    return path


def delete_file_from_storage(storage_path: str) -> bool:
    """Delete a file from Supabase Storage."""
    client = get_supabase_client()
    client.storage.from_("documents").remove([storage_path])
    return True


# ─── Auth Helpers ─────────────────────────────────────────────

def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify a Supabase JWT and return user data."""
    client = get_supabase_client()
    try:
        user_response = client.auth.get_user(token)
        if user_response and user_response.user:
            return {
                "id": str(user_response.user.id),
                "email": user_response.user.email,
            }
    except Exception:
        return None
    return None


# ─── Health Check ─────────────────────────────────────────────

def check_supabase_health() -> bool:
    """Simple connectivity check."""
    try:
        client = get_supabase_client()
        client.table("documents").select("id").limit(1).execute()
        return True
    except Exception:
        return False
