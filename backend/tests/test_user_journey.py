import time
import json
import httpx

BASE_URL = "http://localhost:8000"

def run_user_journey():
    timestamp = int(time.time())
    email = f"testuser_{timestamp}@searchlab.ai"
    password = "TestPassword2026!"
    name = f"Test User {timestamp % 1000}"

    print(f"=== STEP 1: REGISTERING NEW USER ===")
    print(f"Name: {name}")
    print(f"Email: {email}")

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Register
        reg_resp = client.post("/auth/register", json={
            "name": name,
            "email": email,
            "password": password
        })
        if reg_resp.status_code not in (200, 201):
            print(f"[FAIL] Register failed: {reg_resp.status_code} {reg_resp.text}")
            return
        user_data = reg_resp.json()
        user_info = user_data.get("user", user_data)
        print(f"[PASS] User registered successfully! User ID: {user_info.get('id')}, Role: {user_info.get('role')}")

        # 2. Login
        print(f"\n=== STEP 2: LOGGING IN ===")
        login_resp = client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        if login_resp.status_code != 200:
            print(f"[FAIL] Login failed: {login_resp.status_code} {login_resp.text}")
            return
        tokens = login_resp.json()
        token = tokens.get("token") or tokens.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[PASS] Logged in successfully! Received JWT access token: {token[:20]}...")

        # 3. Upload random document
        print(f"\n=== STEP 3: UPLOADING NEW DOCUMENT ===")
        doc_title = "Corporate Travel & Expense Policy 2026.txt"
        doc_content = (
            "Corporate Travel & Expense Policy 2026:\n\n"
            "1. Meal Allowance: Employees traveling for official business may claim a daily meal allowance of up to $75 per day.\n"
            "2. Flight Bookings: All domestic and international flight tickets must be booked in Economy Class at least 14 days in advance.\n"
            "3. Hotel Accommodation: Hotel room expenses are reimbursable up to a maximum limit of $200 per night with valid tax invoices.\n"
            "4. Local Transportation: Taxi and rideshare services like Uber and Lyft are covered for official client visits up to $50 per day."
        )

        upload_resp = client.post("/documents/text", json={
            "name": doc_title,
            "text": doc_content
        }, headers=headers)

        if upload_resp.status_code not in (200, 201, 202):
            print(f"[FAIL] Upload failed: {upload_resp.status_code} {upload_resp.text}")
            return
        doc_data = upload_resp.json()
        doc_id = doc_data["id"]
        print(f"[PASS] Document uploaded and processed! ID: {doc_id}, Title: {doc_title}, Status: {doc_data.get('status')}")

        # Verify document in list
        docs_resp = client.get("/documents", headers=headers)
        user_docs = docs_resp.json()
        print(f"[PASS] Retrieved user's document list: {len(user_docs)} document(s) ready.")

        # 4. Ask simple question
        question = "How much can employees claim per day for meals?"
        print(f"\n=== STEP 4: ASKING SIMPLE QUESTION ===")
        print(f"Question: \"{question}\"")

        start_time = time.time()
        with client.stream("POST", "/ask", json={
            "question": question,
            "document_ids": [doc_id]
        }, headers=headers) as response:
            if response.status_code != 200:
                print(f"[FAIL] /ask request failed with {response.status_code}")
                return

            sources = []
            tokens_list = []
            current_event = None

            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("event: "):
                    current_event = line[7:].strip()
                elif line.startswith("data: "):
                    data_str = line[6:].strip()
                    if current_event == "sources":
                        try:
                            sources = json.loads(data_str)
                        except Exception:
                            pass
                    elif current_event == "token":
                        tokens_list.append(data_str)
                    elif current_event == "done":
                        break

        latency = time.time() - start_time
        full_answer = "".join(tokens_list).strip()

        print(f"\n[PASS] Streaming response received in {latency:.2f}s!")
        print(f"\n--- RETRIEVED SOURCES ({len(sources)}) ---")
        for idx, src in enumerate(sources, 1):
            s_name = src.get('name') or src.get('document_name') or "Document"
            s_text = src.get('text') or src.get('content') or ""
            print(f"[{idx}] {s_name} (Similarity: {src.get('score', 0):.3f})")
            print(f"    Excerpt: {s_text[:120]}...")

        print(f"\n--- GENERATED GROUNDED ANSWER ---")
        print(full_answer)
        print(f"---------------------------------")

        # Save journey report to JSON
        journey_result = {
            "user": {
                "id": user_data.get("id"),
                "name": name,
                "email": email,
                "password": password
            },
            "document": {
                "id": doc_id,
                "title": doc_title,
                "status": doc_data.get("status")
            },
            "query": {
                "question": question,
                "answer": full_answer,
                "sources_count": len(sources),
                "latency_seconds": round(latency, 2)
            }
        }
        with open("c:/Users/user/Desktop/new website/SearchLab.AI/backend/journey_result.json", "w", encoding="utf-8") as f:
            json.dump(journey_result, f, indent=2)

        print("\n=== USER JOURNEY TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_user_journey()
