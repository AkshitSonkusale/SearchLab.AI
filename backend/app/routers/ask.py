import json
import logging
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.config import get_settings
from app.db import execute_query
from app.auth import get_current_user
from app.rag.embed import embed_query
from app.rag.retrieve import retrieve_top_chunks
from app.rag.generate import generate_grounded_answer, find_evidence_sentence
from app.rag.conflicts import detect_conflicts

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/ask", tags=["Query & RAG"])

class AskRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None

def extract_key_terms(text: str) -> List[str]:
    stopwords = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how", "the", "and", "is", "in", "to", "for", "with", "does", "can", "should"}
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return [w for w in words if w not in stopwords][:5]

@router.post("")
async def ask_question(
    req: AskRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    question_text = req.question.strip()

    if not question_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "empty_question", "message": "Question text cannot be empty."}
        )

    # Security: Validate document ownership to prevent IDOR probing
    if req.document_ids:
        owned_docs = execute_query(
            "SELECT id FROM documents WHERE user_id = %s::uuid AND id = ANY(%s::uuid[])",
            (user_id, req.document_ids),
            fetch_all=True
        )
        if len(owned_docs) < len(req.document_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "One or more selected documents do not exist or belong to another account."}
            )

    # Get search scope stats
    stats_row = execute_query(
        """
        SELECT 
            COUNT(DISTINCT c.document_id) as total_docs,
            COUNT(c.id) as total_chunks
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.user_id = %s::uuid AND d.status = 'ready'
          AND (%s::uuid[] IS NULL OR c.document_id = ANY(%s::uuid[]));
        """,
        (user_id, req.document_ids, req.document_ids),
        fetch_one=True
    )
    passages_searched = stats_row["total_chunks"] if stats_row else 0
    documents_searched = stats_row["total_docs"] if stats_row else 0

    key_terms = extract_key_terms(question_text)

    # 1. Embed question
    query_vector = embed_query(question_text)

    # 2. Retrieve top chunks via pgvector
    top_chunks = retrieve_top_chunks(
        query_vector=query_vector,
        user_id=user_id,
        document_ids=req.document_ids,
        limit=settings.top_k_chunks
    )

    best_score = top_chunks[0]["score"] if top_chunks else 0.0

    async def sse_event_stream():
        # Condition A: No chunks found or below relevance threshold
        if not top_chunks or best_score < settings.relevance_threshold:
            # Send top 2 closest chunks as sources if available
            closest_sources = []
            for idx, c in enumerate(top_chunks[:2]):
                closest_sources.append({
                    "id": c["id"],
                    "name": c["document_name"],
                    "passage_id": idx + 1,
                    "text": c["text"],
                    "score": c["score"],
                    "evidence_sentence": c["text"][:160]
                })

            yield f"event: sources\ndata: {json.dumps(closest_sources)}\n\n"

            not_found_msg = "This isn't in your documents."
            yield f"event: token\ndata: {json.dumps(not_found_msg)}\n\n"

            done_payload = {
                "answer": not_found_msg,
                "found": False,
                "search": {
                    "terms": key_terms,
                    "passages_searched": passages_searched,
                    "documents_searched": documents_searched,
                    "best_score": best_score,
                    "threshold": settings.relevance_threshold
                },
                "conflicts": []
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

            # Persist question to history
            execute_query(
                """
                INSERT INTO questions (user_id, question, answer, found, sources, search_info, asked_at)
                VALUES (%s::uuid, %s, %s, false, %s::jsonb, %s::jsonb, now())
                """,
                (user_id, question_text, not_found_msg, json.dumps(closest_sources), json.dumps(done_payload["search"]))
            )
            return

        # Condition B: High similarity score, proceed with Groq grounded generation
        # Prepare candidate sources
        candidate_sources = []
        for idx, c in enumerate(top_chunks):
            candidate_sources.append({
                "id": c["id"],
                "name": c["document_name"],
                "document_id": c["document_id"],
                "passage_id": idx + 1,
                "text": c["text"],
                "score": c["score"]
            })

        # Generate answer from Groq
        full_answer_parts = []
        async for token in generate_grounded_answer(question_text, candidate_sources):
            full_answer_parts.append(token)

        full_answer = "".join(full_answer_parts).strip()

        # Handle NOT_FOUND model output
        if "NOT_FOUND" in full_answer or len(full_answer) < 5:
            closest_sources = []
            for idx, s in enumerate(candidate_sources[:2]):
                closest_sources.append({
                    "id": s["id"],
                    "name": s["name"],
                    "passage_id": idx + 1,
                    "text": s["text"],
                    "score": s["score"],
                    "evidence_sentence": s["text"][:160]
                })

            yield f"event: sources\ndata: {json.dumps(closest_sources)}\n\n"
            not_found_msg = "This isn't in your documents."
            yield f"event: token\ndata: {json.dumps(not_found_msg)}\n\n"

            done_payload = {
                "answer": not_found_msg,
                "found": False,
                "search": {
                    "terms": key_terms,
                    "passages_searched": passages_searched,
                    "documents_searched": documents_searched,
                    "best_score": best_score,
                    "threshold": settings.relevance_threshold
                },
                "conflicts": []
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

            execute_query(
                """
                INSERT INTO questions (user_id, question, answer, found, sources, search_info, asked_at)
                VALUES (%s::uuid, %s, %s, false, %s::jsonb, %s::jsonb, now())
                """,
                (user_id, question_text, not_found_msg, json.dumps(closest_sources), json.dumps(done_payload["search"]))
            )
            return

        # Grounded answer successfully produced:
        # Calculate evidence sentence for each source
        final_sources = []
        for s in candidate_sources:
            evidence = find_evidence_sentence(s["text"], full_answer)
            final_sources.append({
                "id": s["id"],
                "name": s["name"],
                "document_id": s["document_id"],
                "passage_id": s["passage_id"],
                "text": s["text"],
                "score": s["score"],
                "evidence_sentence": evidence
            })

        # Detect conflicts across distinct sources
        conflicts = detect_conflicts(final_sources, question_text)

        # 1. Send sources event first
        yield f"event: sources\ndata: {json.dumps(final_sources)}\n\n"

        # 2. Stream tokens
        for token in full_answer_parts:
            yield f"event: token\ndata: {json.dumps(token)}\n\n"

        # 3. Send done event
        done_payload = {
            "answer": full_answer,
            "found": True,
            "search": {
                "terms": key_terms,
                "passages_searched": passages_searched,
                "documents_searched": documents_searched,
                "best_score": best_score,
                "threshold": settings.relevance_threshold
            },
            "conflicts": conflicts
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        # Persist to questions table
        execute_query(
            """
            INSERT INTO questions (user_id, question, answer, found, sources, search_info, asked_at)
            VALUES (%s::uuid, %s, %s, true, %s::jsonb, %s::jsonb, now())
            """,
            (user_id, question_text, full_answer, json.dumps(final_sources), json.dumps(done_payload["search"]))
        )

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
