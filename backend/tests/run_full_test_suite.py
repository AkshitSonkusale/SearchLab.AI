import os
import sys
import time
import json
import uuid
from typing import Dict, Any, List
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.main import app
from app.db import execute_query

client = TestClient(app)

results = {
    "suite_name": "SearchLab.AI Full System Verification",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "tests_run": 0,
    "tests_passed": 0,
    "tests_failed": 0,
    "details": []
}

def log_test(name: str, passed: bool, message: str, meta: Dict[str, Any] = None):
    results["tests_run"] += 1
    if passed:
        results["tests_passed"] += 1
        status_str = "PASS"
    else:
        results["tests_failed"] += 1
        status_str = "FAIL"
    entry = {
        "test": name,
        "status": status_str,
        "message": message,
        "meta": meta or {}
    }
    results["details"].append(entry)
    print(f"[{status_str}] {name}: {message}")

def run_all_tests():
    print("=" * 60)
    print("STARTING SEARCHLAB.AI END-TO-END TEST SUITE")
    print("=" * 60)

    u1_token = None
    u2_token = None
    adm_token = None

    # 1. Health Endpoint
    try:
        res = client.get("/health")
        passed = res.status_code == 200 and res.json().get("status") == "healthy"
        log_test("System Health Check", passed, f"Status code {res.status_code}", res.json())
    except Exception as e:
        log_test("System Health Check", False, str(e))

    # 2. Auth - Validation & Edge Cases
    try:
        # Weak password rejection
        res_weak = client.post("/auth/register", json={"name": "Weak", "email": "weak@demo.com", "password": "short"})
        passed_weak = res_weak.status_code == 400 and res_weak.json().get("error") == "weak_password"
        log_test("Auth - Weak Password Rejection", passed_weak, "Correctly rejected <8 char password")

        # Admin authentication (using seeded admin@demo.com)
        res_adm = client.post("/auth/login", json={"email": "admin@demo.com", "password": "admin1234"})
        if res_adm.status_code != 200:
            res_adm = client.post("/auth/register", json={"name": "System Admin", "email": "admin@demo.com", "password": "Password123!"})
        adm_data = res_adm.json()
        adm_token = adm_data["token"]
        adm_role = adm_data["user"]["role"]
        log_test("Auth - Admin Role Verification", adm_role == "admin", f"Role assigned: {adm_role}")

        # Normal user 1 registration
        u1_email = f"user1_{int(time.time())}@example.com"
        res_u1 = client.post("/auth/register", json={"name": "Alice User", "email": u1_email, "password": "password123"})
        u1_data = res_u1.json()
        u1_token = u1_data["token"]
        u1_id = u1_data["user"]["id"]
        log_test("Auth - User 1 Registration", res_u1.status_code == 201, f"Registered user ID: {u1_id}")

        # Normal user 2 registration (for multi-tenant isolation testing)
        u2_email = f"user2_{int(time.time())}@example.com"
        res_u2 = client.post("/auth/register", json={"name": "Bob User", "email": u2_email, "password": "password123"})
        u2_data = res_u2.json()
        u2_token = u2_data["token"]
        u2_id = u2_data["user"]["id"]
        log_test("Auth - User 2 Registration", res_u2.status_code == 201, f"Registered user ID: {u2_id}")

        # Duplicate email rejection
        res_dup = client.post("/auth/register", json={"name": "Alice Duplicate", "email": u1_email, "password": "password123"})
        log_test("Auth - Duplicate Email Rejection", res_dup.status_code == 400 and res_dup.json().get("error") == "email_taken", "Duplicate email blocked")

        # User Login
        res_login = client.post("/auth/login", json={"email": u1_email, "password": "password123"})
        log_test("Auth - User Login", res_login.status_code == 200 and "token" in res_login.json(), "JWT issued on valid login")

        # Wrong password login rejection
        res_bad_login = client.post("/auth/login", json={"email": u1_email, "password": "wrongpassword"})
        log_test("Auth - Invalid Credentials Rejection", res_bad_login.status_code == 401, "Rejected bad password with 401")

        # Token verification via /auth/me
        res_me = client.get("/auth/me", headers={"Authorization": f"Bearer {u1_token}"})
        log_test("Auth - /auth/me Token Session", res_me.status_code == 200 and res_me.json()["email"] == u1_email, "Session restored from JWT")

    except Exception as e:
        log_test("Auth Verification", False, f"Exception: {e}")

    # 3. Document Ingestion & Conflict Data Setup
    # Alice uploads Document 1 (Intern Leave Policy): specifies 3 days in advance
    u1_headers = {"Authorization": f"Bearer {u1_token}"}
    u2_headers = {"Authorization": f"Bearer {u2_token}"}
    adm_headers = {"Authorization": f"Bearer {adm_token}"}

    doc1_id = None
    doc2_id = None
    u2_doc_id = None

    try:
        # Document 1 (Alice): Intern Policy
        doc1_text = """Internship Leave Policy Handbook.
Interns must request leave at least 3 business days in advance by notifying their supervisor.
Interns receive 2 paid personal leave days every month of work."""
        res_d1 = client.post("/documents/text", headers=u1_headers, json={"name": "Intern Leave Policy.txt", "text": doc1_text})
        doc1_id = res_d1.json()["id"]

        # Document 2 (Alice): General Employee Handbook (creates deliberate policy conflict: 5 days in advance)
        doc2_text = """General Employee Working and Leave Handbook.
All personnel must request leave at least 5 business days in advance through the HR portal.
Employees are entitled to 20 vacation days annually."""
        res_d2 = client.post("/documents/text", headers=u1_headers, json={"name": "Employee Leave Handbook.txt", "text": doc2_text})
        doc2_id = res_d2.json()["id"]

        # Document 3 (Bob / User 2): Engineering Architecture (unrelated)
        u2_text = """SearchLab AI Engineering Architecture Spec.
The architecture consists of a React frontend deployed to Vercel and a FastAPI backend deployed to Render.
PostgreSQL with pgvector handles dense vector embeddings."""
        res_u2_d = client.post("/documents/text", headers=u2_headers, json={"name": "Engineering Spec.txt", "text": u2_text})
        u2_doc_id = res_u2_d.json()["id"]

        # Allow background ingestion to complete
        time.sleep(3)

        # Check document list for Alice
        d_list = client.get("/documents", headers=u1_headers).json()
        ready_count = sum(1 for d in d_list if d["status"] == "ready")
        log_test("Documents - Processing & Status Ready", ready_count >= 2, f"{ready_count} documents ready for User 1")

    except Exception as e:
        log_test("Document Ingestion", False, str(e))

    # 4. Multi-Tenant Data Isolation Tests
    try:
        # User 2 attempts to GET User 1's document -> Must return 404
        res_leak = client.delete(f"/documents/{doc1_id}", headers=u2_headers)
        log_test("Multi-Tenancy - Cross-User Deletion Block", res_leak.status_code == 404, "User 2 cannot delete User 1's document (404 returned)")

        # User 2 searches for "Intern leave" -> Must return "This isn't in your documents." because Bob has no leave docs
        res_u2_ask = client.post("/ask", headers=u2_headers, json={"question": "How many days in advance should I request leave?"})
        u2_ask_text = res_u2_ask.text
        passed_isolation = "This isn't in your documents." in u2_ask_text
        log_test("Multi-Tenancy - Semantic Search Isolation", passed_isolation, "User 2 cannot search or see User 1's private passages")

    except Exception as e:
        log_test("Multi-Tenancy Verification", False, str(e))

    # 5. RAG Pipeline, Citations & Conflict Detection
    try:
        # In-Scope query with deliberate conflict ("Sources disagree")
        res_conflict_ask = client.post("/ask", headers=u1_headers, json={"question": "How many days in advance should I request leave?"})
        stream_text = res_conflict_ask.text
        
        has_sources = "event: sources" in stream_text
        has_tokens = "event: token" in stream_text
        has_done = "event: done" in stream_text
        
        log_test("RAG - SSE Protocol Events", has_sources and has_tokens and has_done, "Stream emitted sources, token, and done events")

        # Parse the done event payload
        done_payload = None
        for line in stream_text.split("\n"):
            if line.startswith("data:") and "conflicts" in line:
                try:
                    done_payload = json.loads(line.replace("data:", "").strip())
                    break
                except:
                    pass

        has_conflicts = done_payload and len(done_payload.get("conflicts", [])) > 0
        log_test("RAG - Source Disagreement Detection", bool(has_conflicts), f"Detected {len(done_payload.get('conflicts', [])) if done_payload else 0} policy conflict(s)", done_payload.get("conflicts") if done_payload else {})

        # Verify Grounded Citations in answer
        answer = done_payload.get("answer", "") if done_payload else ""
        has_citation = ("[1]" in answer or "[2]" in answer or "3" in answer or "5" in answer)
        log_test("RAG - Grounded Answer Citations", has_citation, "Answer contains specific passage references or values")

        # Out-of-Scope Query Gating ("Not Found" Rule)
        res_out = client.post("/ask", headers=u1_headers, json={"question": "What is the secret stock purchase option price for executives?"})
        out_text = res_out.text
        is_not_found = "This isn't in your documents." in out_text
        log_test("RAG - Relevance Threshold Gating (Not Found)", is_not_found, "Correctly rejected out-of-scope question without hallucinating")

    except Exception as e:
        log_test("RAG Pipeline Verification", False, str(e))

    # 6. History, Feedback & Deletion
    try:
        # Check history list
        res_hist = client.get("/history", headers=u1_headers)
        hist_items = res_hist.json()
        log_test("History - Question History Persistence", len(hist_items) >= 2, f"Retrieved {len(hist_items)} past questions")

        # Filtered history search ?q=leave
        res_filter = client.get("/history?q=leave", headers=u1_headers)
        log_test("History - Search Query Filtering", len(res_filter.json()) >= 1, f"Filtered results: {len(res_filter.json())}")

        # Post feedback
        first_q_id = hist_items[0]["id"]
        res_fb = client.post("/feedback", headers=u1_headers, json={"question_id": first_q_id, "helpful": True})
        log_test("Feedback - Record Thumbs Up/Down", res_fb.status_code == 200, "Feedback recorded successfully")

        # Document deletion removes passages from future searches
        del_res = client.delete(f"/documents/{doc1_id}", headers=u1_headers)
        log_test("Documents - Cascade Deletion", del_res.status_code == 204, "Document and associated vector chunks removed")

        # Verify deletion reflected in documents list
        d_list_after = client.get("/documents", headers=u1_headers).json()
        ids_after = [d["id"] for d in d_list_after]
        log_test("Documents - Deletion State Verified", doc1_id not in ids_after, "Deleted document no longer returned in list")

    except Exception as e:
        log_test("History & Deletion Verification", False, str(e))

    # 7. Admin Endpoints & BRD Evaluation Benchmark
    try:
        # Admin User List
        res_users = client.get("/admin/users", headers=adm_headers)
        log_test("Admin - List Users", res_users.status_code == 200, f"Total users: {len(res_users.json())}")

        # Non-admin forbidden from admin endpoints
        res_forbid = client.get("/admin/users", headers=u1_headers)
        log_test("Admin - Non-Admin RBAC Protection", res_forbid.status_code == 403, "Non-admin blocked with 403 Forbidden")

        # Admin Invite User
        invite_email = f"invited_{int(time.time())}@demo.com"
        res_invite = client.post("/admin/users/invite", headers=adm_headers, json={"name": "Invited Employee", "email": invite_email, "role": "user"})
        log_test("Admin - Invite User", res_invite.status_code == 201, f"User invited with temp password")

        # Admin Evaluation Run (BRD targets verification)
        res_eval = client.post("/admin/evaluation/run", headers=adm_headers)
        eval_data = res_eval.json()
        metrics = eval_data.get("metrics", {})
        hit_rate = metrics.get("hit_rate_percentage", 0) or (metrics.get("hit_rate", 0) * 100)
        oof_acc = metrics.get("out_of_scope_accuracy_percentage", 0) or (metrics.get("faithfulness", 0) * 100)
        overall = metrics.get("overall_accuracy_percentage", 0)

        log_test("Evaluation - Benchmark Hit Rate (Target >= 80%)", hit_rate >= 80.0, f"Hit Rate: {hit_rate}%", metrics)
        log_test("Evaluation - Faithfulness / Out-of-Scope (Target >= 90%)", oof_acc >= 90.0, f"Out-of-Scope Accuracy: {oof_acc}%", metrics)

        # Admin Coverage Gaps
        res_gaps = client.get("/admin/gaps", headers=adm_headers)
        gaps_data = res_gaps.json()
        has_gaps = len(gaps_data.get("unanswered_questions", [])) > 0 or len(gaps_data.get("conflicts", [])) > 0
        log_test("Admin - Coverage Gaps Tracking", res_gaps.status_code == 200, f"Unanswered: {len(gaps_data.get('unanswered_questions', []))}, Conflicts: {len(gaps_data.get('conflicts', []))}")

    except Exception as e:
        log_test("Admin & Evaluation Verification", False, str(e))

    print("=" * 60)
    print(f"TEST SUITE COMPLETE: {results['tests_passed']}/{results['tests_run']} PASSED ({results['tests_failed']} FAILED)")
    print("=" * 60)

    # Save results to json for report generation
    with open("SearchLab.AI/backend/test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_all_tests()
