import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.config import settings
from app.db import execute_query
from app.auth import require_admin, get_password_hash
from app.rag.embed import embed_query
from app.rag.retrieve import retrieve_top_chunks

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

class InviteUserRequest(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"

class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None

@router.get("/users")
async def list_users(admin: Dict[str, Any] = Depends(require_admin)):
    users = execute_query(
        """
        SELECT 
            id,
            name,
            email,
            role,
            active,
            to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as created_at,
            to_char(last_active_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as last_active_at
        FROM users
        ORDER BY created_at ASC;
        """,
        fetch_all=True
    )
    return [
        {
            "id": str(u["id"]),
            "name": u["name"],
            "email": u["email"],
            "role": u["role"],
            "active": u["active"],
            "created_at": u["created_at"],
            "last_active_at": u["last_active_at"]
        }
        for u in (users or [])
    ]

@router.post("/users/invite", status_code=status.HTTP_201_CREATED)
async def invite_user(
    req: InviteUserRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    existing = execute_query("SELECT id FROM users WHERE email = %s", (req.email.lower(),), fetch_one=True)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "email_taken", "message": "A user with this email already exists."}
        )

    # Set temporary random password
    temp_password = str(uuid.uuid4())[:12]
    pwd_hash = get_password_hash(temp_password)
    role = req.role if req.role in ["user", "admin"] else "user"

    new_user = execute_query(
        """
        INSERT INTO users (name, email, password_hash, role, active, created_at, last_active_at)
        VALUES (%s, %s, %s, %s, true, now(), now())
        RETURNING id, name, email, role, active, to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as created_at
        """,
        (req.name.strip(), req.email.lower(), pwd_hash, role),
        fetch_one=True
    )

    return {
        "id": str(new_user["id"]),
        "name": new_user["name"],
        "email": new_user["email"],
        "role": new_user["role"],
        "active": new_user["active"],
        "created_at": new_user["created_at"]
    }

@router.patch("/users/{id}")
async def update_user(
    id: str,
    req: UpdateUserRequest,
    admin: Dict[str, Any] = Depends(require_admin)
):
    # Rule from backend guide: block changing/deactivating yourself
    if id == admin["id"] and req.active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "cannot_deactivate_self", "message": "You cannot deactivate your own admin account."}
        )

    target_user = execute_query("SELECT id FROM users WHERE id = %s", (id,), fetch_one=True)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "User not found."}
        )

    updates = []
    params = []
    if req.role is not None and req.role in ["user", "admin"]:
        updates.append("role = %s")
        params.append(req.role)
    if req.active is not None:
        updates.append("active = %s")
        params.append(req.active)

    if updates:
        params.append(id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING id, name, email, role, active"
        updated = execute_query(sql, tuple(params), fetch_one=True)
        return {
            "id": str(updated["id"]),
            "name": updated["name"],
            "email": updated["email"],
            "role": updated["role"],
            "active": updated["active"]
        }

    return {"message": "No updates applied."}

@router.post("/evaluation/run")
async def run_evaluation(admin: Dict[str, Any] = Depends(require_admin)):
    """
    Executes benchmark accuracy run against test set questions.
    Checks:
    1. Hit Rate: percentage of in-scope questions where correct document appears in top 5.
    2. Faithfulness: percentage of out-of-scope questions correctly answered as 'not found'.
    """
    admin_id = admin["id"]
    test_questions = execute_query(
        "SELECT id, question, expected_document FROM eval_questions ORDER BY id ASC",
        fetch_all=True
    )

    if not test_questions:
        # Default seed questions if none in table
        test_questions = [
            {"id": 1, "question": "How many days in advance should I request leave?", "expected_document": "leave"},
            {"id": 2, "question": "What is the CEO's salary?", "expected_document": None},
            {"id": 3, "question": "What is the intern working hours policy?", "expected_document": "intern"},
            {"id": 4, "question": "What is the company stock ticker?", "expected_document": None}
        ]

    total_in_scope = 0
    correct_in_scope = 0
    total_out_scope = 0
    correct_out_scope = 0
    results_detail = []

    for item in test_questions:
        q_text = item["question"]
        expected = item.get("expected_document")

        q_vec = embed_query(q_text)
        retrieved = retrieve_top_chunks(q_vec, user_id=None, limit=5)
        best_score = retrieved[0]["score"] if retrieved else 0.0

        if expected:
            total_in_scope += 1
            # Check if expected document is in top 5
            matched = any(expected.lower() in r["document_name"].lower() for r in retrieved)
            if matched and best_score >= settings.relevance_threshold:
                correct_in_scope += 1
                status_str = "pass"
            else:
                status_str = "fail"
        else:
            total_out_scope += 1
            # Out-of-scope: should be not found or score below threshold or unrelated to expected docs
            if not retrieved or best_score < max(settings.relevance_threshold, 0.55):
                correct_out_scope += 1
                status_str = "pass"
            else:
                status_str = "fail"

        results_detail.append({
            "question": q_text,
            "expected": expected,
            "status": status_str,
            "best_score": best_score
        })

    hit_rate = round(correct_in_scope / total_in_scope, 2) if total_in_scope > 0 else 1.0
    faithfulness = round(correct_out_scope / total_out_scope, 2) if total_out_scope > 0 else 1.0

    metrics = {
        "hit_rate": hit_rate,
        "hit_rate_percentage": round(hit_rate * 100, 1),
        "faithfulness": faithfulness,
        "out_of_scope_accuracy_percentage": round(faithfulness * 100, 1),
        "total_questions": len(test_questions),
        "in_scope_evaluated": total_in_scope,
        "out_of_scope_evaluated": total_out_scope,
        "target_met": (hit_rate >= 0.80 and faithfulness >= 0.90)
    }

    run_row = execute_query(
        """
        INSERT INTO eval_runs (status, metrics, results, started_at, finished_at)
        VALUES ('completed', %s::jsonb, %s::jsonb, now(), now())
        RETURNING id, status, metrics, results, to_char(finished_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as finished_at
        """,
        (json.dumps(metrics), json.dumps(results_detail)),
        fetch_one=True
    )

    return {
        "id": run_row["id"],
        "status": run_row["status"],
        "metrics": run_row["metrics"],
        "results": run_row["results"],
        "finished_at": run_row["finished_at"]
    }

@router.get("/evaluation/runs/{id}")
async def get_evaluation_run(id: int, admin: Dict[str, Any] = Depends(require_admin)):
    run_row = execute_query(
        """
        SELECT id, status, metrics, results, to_char(finished_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as finished_at
        FROM eval_runs WHERE id = %s
        """,
        (id,),
        fetch_one=True
    )
    if not run_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Evaluation run not found."}
        )
    return run_row

@router.get("/gaps")
async def get_coverage_gaps(admin: Dict[str, Any] = Depends(require_admin)):
    """
    Returns unanswered questions grouped for content coverage improvement,
    along with detected source conflicts.
    """
    unanswered = execute_query(
        """
        SELECT question, COUNT(*)::int as count, MAX(asked_at) as last_asked
        FROM questions
        WHERE found = false
        GROUP BY question
        ORDER BY count DESC
        LIMIT 20;
        """,
        fetch_all=True
    )

    conflicts = execute_query(
        """
        SELECT id, doc_a, doc_b, text_a, text_b, example_question, count, to_char(last_seen_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as last_seen_at
        FROM conflicts
        ORDER BY last_seen_at DESC
        LIMIT 20;
        """,
        fetch_all=True
    )

    return {
        "unanswered_questions": [
            {
                "question": u["question"],
                "count": u["count"],
                "last_asked": str(u["last_asked"])
            }
            for u in (unanswered or [])
        ],
        "conflicts": [
            {
                "id": c["id"],
                "doc_a": c["doc_a"],
                "doc_b": c["doc_b"],
                "text_a": c["text_a"],
                "text_b": c["text_b"],
                "example_question": c["example_question"],
                "count": c["count"],
                "last_seen_at": c["last_seen_at"]
            }
            for c in (conflicts or [])
        ]
    }
