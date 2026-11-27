import os
import sys
import time
import httpx
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.main import app

client = TestClient(app)

def test_full_pipeline():
    print("\n--- 1. Testing GET /health ---")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("Health check response:", res.json())

    print("\n--- 2. Testing Auth Registration (Admin) ---")
    admin_email = f"admin_test_{int(time.time())}@example.com"
    reg_res = client.post(
        "/auth/register",
        json={"name": "Nandhishwar Admin", "email": admin_email, "password": "supersecurepassword123"}
    )
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    admin_data = reg_res.json()
    token = admin_data["token"]
    user_id = admin_data["user"]["id"]
    print("Admin registered successfully! Role:", admin_data["user"]["role"])

    headers = {"Authorization": f"Bearer {token}"}

    print("\n--- 3. Testing GET /auth/me ---")
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200, f"Get /auth/me failed: {me_res.text}"
    print("Auth /me verified:", me_res.json()["email"])

    print("\n--- 4. Testing Ingestion: POST /documents/text ---")
    policy_text = """SearchLab AI Intern Policy and Working Guidelines.
Intern leave requests must be submitted at least 3 business days in advance to the assigned project mentor.
Interns are entitled to 2 days of paid personal time off per month during their internship duration.
Working hours are flexible between 9:00 AM and 6:00 PM Monday through Friday.
Daily standup meetings occur promptly at 10:00 AM in the engineering virtual room."""

    doc_res = client.post(
        "/documents/text",
        headers=headers,
        json={"name": "Intern Policy.txt", "text": policy_text}
    )
    assert doc_res.status_code == 202, f"Document ingestion failed: {doc_res.text}"
    doc_id = doc_res.json()["id"]
    print(f"Document submitted for processing! Document ID: {doc_id}")

    # Wait 2 seconds for background embedding & storage to finish
    time.sleep(2)

    print("\n--- 5. Testing GET /documents ---")
    docs_res = client.get("/documents", headers=headers)
    assert docs_res.status_code == 200, f"List documents failed: {docs_res.text}"
    docs_list = docs_res.json()
    print(f"Documents found: {len(docs_list)}, first doc status: {docs_list[0]['status']}, passages: {docs_list[0]['passages']}")
    assert docs_list[0]["status"] == "ready", "Document should be in 'ready' status"
    assert docs_list[0]["passages"] > 0, "Document should have passages indexed"

    print("\n--- 6. Testing In-Scope RAG Query: POST /ask ---")
    ask_res = client.post(
        "/ask",
        headers=headers,
        json={"question": "How many days in advance should I request leave?", "document_ids": None}
    )
    assert ask_res.status_code == 200, f"Ask failed: {ask_res.text}"
    # Read SSE events from streaming body
    sse_text = ask_res.text
    print("SSE Stream Output received:\n" + sse_text[:300] + "...")
    assert "event: sources" in sse_text
    assert "event: token" in sse_text
    assert "event: done" in sse_text
    assert "3" in sse_text or "advance" in sse_text

    print("\n--- 7. Testing Out-of-Scope (Not Found) Query: POST /ask ---")
    out_res = client.post(
        "/ask",
        headers=headers,
        json={"question": "What is the CEO's salary and stock options?", "document_ids": None}
    )
    assert out_res.status_code == 200
    out_sse = out_res.text
    print("Out-of-scope SSE Output preview:\n" + out_sse[:300] + "...")
    assert "This isn't in your documents." in out_sse, "Out of scope query must return 'This isn't in your documents.'"

    print("\n--- 8. Testing GET /history ---")
    hist_res = client.get("/history", headers=headers)
    assert hist_res.status_code == 200
    history_items = hist_res.json()
    print(f"History entries recorded: {len(history_items)}")
    assert len(history_items) >= 2, "Both queries should be in history"

    print("\n--- 9. Testing POST /feedback ---")
    first_q_id = history_items[0]["id"]
    fb_res = client.post(
        "/feedback",
        headers=headers,
        json={"question_id": first_q_id, "helpful": True}
    )
    assert fb_res.status_code == 200
    print("Feedback submission confirmed:", fb_res.json())

    print("\n--- 10. Testing Admin Endpoints: GET /admin/users & GET /admin/gaps ---")
    users_res = client.get("/admin/users", headers=headers)
    assert users_res.status_code == 200
    print(f"Admin users count: {len(users_res.json())}")

    gaps_res = client.get("/admin/gaps", headers=headers)
    assert gaps_res.status_code == 200
    print("Admin coverage gaps:", gaps_res.json())

    print("\n==========================================")
    print("ALL TESTS PASSED! BACKEND IS 100% OPERATIONAL.")
    print("==========================================")

if __name__ == "__main__":
    test_full_pipeline()
