import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.db import execute_query
from app.auth import get_current_user

router = APIRouter(tags=["History & Feedback"])

class FeedbackRequest(BaseModel):
    question_id: str
    helpful: bool

@router.get("/history")
async def get_history(
    q: Optional[str] = Query(None, description="Search term for past questions"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = """
        SELECT id, question, answer, found, sources, search_info, asked_at
        FROM questions
        WHERE user_id = %s::uuid 
          AND (question ILIKE %s OR answer ILIKE %s)
        ORDER BY asked_at DESC
        LIMIT 50;
        """
        rows = execute_query(query, (user_id, search_pattern, search_pattern), fetch_all=True)
    else:
        query = """
        SELECT id, question, answer, found, sources, search_info, asked_at
        FROM questions
        WHERE user_id = %s::uuid
        ORDER BY asked_at DESC
        LIMIT 50;
        """
        rows = execute_query(query, (user_id,), fetch_all=True)

    results = []
    for r in (rows or []):
        results.append({
            "id": str(r["id"]),
            "question": r["question"],
            "answer": r["answer"],
            "found": r["found"],
            "sources": r["sources"] if isinstance(r["sources"], (list, dict)) else json.loads(r["sources"] or "[]"),
            "search_info": r["search_info"] if isinstance(r["search_info"], dict) else json.loads(r["search_info"] or "{}"),
            "asked_at": r["asked_at"].isoformat() if r["asked_at"] else None
        })
    return results

@router.get("/history/{question_id}")
async def get_history_detail(
    question_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    row = execute_query(
        """
        SELECT id, question, answer, found, sources, search_info, asked_at
        FROM questions
        WHERE id = %s::uuid AND user_id = %s::uuid
        """,
        (question_id, user_id),
        fetch_one=True
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "History entry not found."}
        )

    return {
        "id": str(row["id"]),
        "question": row["question"],
        "answer": row["answer"],
        "found": row["found"],
        "sources": row["sources"] if isinstance(row["sources"], (list, dict)) else json.loads(row["sources"] or "[]"),
        "search_info": row["search_info"] if isinstance(row["search_info"], dict) else json.loads(row["search_info"] or "{}"),
        "asked_at": row["asked_at"].isoformat() if row["asked_at"] else None
    }

@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    execute_query("DELETE FROM questions WHERE user_id = %s::uuid", (user_id,))
    return None

@router.post("/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    # Check question ownership
    q = execute_query(
        "SELECT id FROM questions WHERE id = %s::uuid AND user_id = %s::uuid",
        (req.question_id, user_id),
        fetch_one=True
    )
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Question not found."}
        )

    execute_query(
        """
        INSERT INTO feedback (question_id, user_id, helpful, created_at)
        VALUES (%s::uuid, %s::uuid, %s, now())
        ON CONFLICT (question_id) DO UPDATE 
        SET helpful = EXCLUDED.helpful, created_at = now();
        """,
        (req.question_id, user_id, req.helpful)
    )
    return {"success": True, "message": "Feedback recorded."}
