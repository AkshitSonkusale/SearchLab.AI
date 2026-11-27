import logging
from typing import List, Dict, Any, Optional
from app.db import execute_query

logger = logging.getLogger(__name__)

def retrieve_top_chunks(
    query_vector: List[float],
    user_id: str,
    document_ids: Optional[List[str]] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Searches chunks using pgvector cosine distance (<=>) in PostgreSQL.
    Strictly filters by user_id and 'ready' document status.
    Optionally filters by specific document IDs.
    Returns sorted list of chunks with similarity score: 1 - cosine_distance.
    """
    query_vector_str = f"[{','.join(map(str, query_vector))}]"

    query = """
    SELECT 
        c.id, 
        c.text, 
        c.chunk_index, 
        d.name as document_name, 
        d.id as document_id,
        1 - (c.embedding <=> %s::vector) as score
    FROM chunks c 
    JOIN documents d ON d.id = c.document_id
    WHERE (%s::uuid IS NULL OR c.user_id = %s::uuid)
      AND d.status = 'ready'
      AND (%s::uuid[] IS NULL OR c.document_id = ANY(%s::uuid[]))
    ORDER BY c.embedding <=> %s::vector
    LIMIT %s;
    """

    doc_ids_param = document_ids if document_ids else None

    results = execute_query(
        query,
        (
            query_vector_str,
            user_id,
            user_id,
            doc_ids_param,
            doc_ids_param,
            query_vector_str,
            limit
        ),
        fetch_all=True
    )

    if not results:
        return []

    chunks = []
    for r in results:
        chunks.append({
            "id": r["id"],
            "text": r["text"],
            "chunk_index": r["chunk_index"],
            "document_name": r["document_name"],
            "document_id": str(r["document_id"]),
            "score": round(float(r["score"]), 4)
        })

    return chunks
