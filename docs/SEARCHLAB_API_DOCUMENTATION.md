# SEARCHLAB.AI — REST & SSE API SPECIFICATION

**API Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api` (Local) / `https://searchlab-backend.onrender.com/api` (Production)  
**Protocol:** HTTPS / REST + Server-Sent Events (SSE)  
**Authentication Scheme:** `Authorization: Bearer <JWT_ACCESS_TOKEN>`  

---

## 1. Authentication Endpoints

### 1.1 Register New User
Creates a new user account with validated credentials.

- **Method:** `POST`
- **Route:** `/api/auth/register`
- **Auth Required:** No
- **Rate Limit:** 15 requests / minute
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Validation Rules:**
  - `email`: Valid RFC 5322 email syntax.
  - `password`: Minimum 8 characters.
- **Success Response (`201 Created`):**
  ```json
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "email": "user@example.com",
    "role": "user",
    "created_at": "2026-11-27T10:00:00.000Z"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Email already registered.
  - `422 Unprocessable Entity`: Validation failure (e.g. password < 8 characters).

---

### 1.2 User Login
Authenticates credentials and returns a signed JWT access token.

- **Method:** `POST`
- **Route:** `/api/auth/login`
- **Auth Required:** No
- **Rate Limit:** 15 requests / minute
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Success Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "role": "user"
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Invalid credentials.

---

### 1.3 Get Current User Profile
Returns account profile data for the active Bearer token.

- **Method:** `GET`
- **Route:** `/api/auth/me`
- **Auth Required:** Yes (`Bearer <token>`)
- **Success Response (`200 OK`):**
  ```json
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "email": "user@example.com",
    "role": "user"
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Missing, expired, or invalid token.

---

### 1.4 Logout
Revokes the current JWT access token.

- **Method:** `POST`
- **Route:** `/api/auth/logout`
- **Auth Required:** Yes (`Bearer <token>`)
- **Success Response (`200 OK`):**
  ```json
  {
    "message": "Logged out successfully"
  }
  ```

---

## 2. Document Management Endpoints

### 2.1 Upload Document
Uploads a document, extracts text, chunks content, generates vector embeddings, and stores records.

- **Method:** `POST`
- **Route:** `/api/documents/upload`
- **Auth Required:** Yes (`Bearer <token>`)
- **Content-Type:** `multipart/form-data`
- **Request Parameters:**
  - `file`: Binary file upload (`.pdf`, `.docx`, `.txt`). Max size: 25MB.
- **Success Response (`201 Created`):**
  ```json
  {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "filename": "quarterly_earnings.pdf",
    "status": "processed",
    "page_count": 12,
    "chunk_count": 48,
    "created_at": "2026-11-27T10:05:00.000Z"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Unsupported file format, corrupted file, or magic byte mismatch.
  - `413 Payload Too Large`: File exceeds 25MB.

---

### 2.2 List User Documents
Returns all documents owned by the authenticated user.

- **Method:** `GET`
- **Route:** `/api/documents/`
- **Auth Required:** Yes (`Bearer <token>`)
- **Success Response (`200 OK`):**
  ```json
  [
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "filename": "quarterly_earnings.pdf",
      "mime_type": "application/pdf",
      "file_size": 1048576,
      "status": "processed",
      "page_count": 12,
      "chunk_count": 48,
      "created_at": "2026-11-27T10:05:00.000Z"
    }
  ]
  ```

---

### 2.3 Get Document Details
Retrieves metadata and status for a specific document.

- **Method:** `GET`
- **Route:** `/api/documents/{doc_id}`
- **Auth Required:** Yes (`Bearer <token>`)
- **Success Response (`200 OK`):**
  ```json
  {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "filename": "quarterly_earnings.pdf",
    "status": "processed",
    "page_count": 12,
    "chunk_count": 48
  }
  ```
- **Error Responses:**
  - `404 Not Found`: Document does not exist or belongs to another user.

---

### 2.4 Get Document Chunks
Retrieves all text chunks and page associations for a document.

- **Method:** `GET`
- **Route:** `/api/documents/{doc_id}/chunks`
- **Auth Required:** Yes (`Bearer <token>`)
- **Success Response (`200 OK`):**
  ```json
  [
    {
      "id": "3d5f9b4e-2a1c-4e8d-9f0a-1b2c3d4e5f6a",
      "chunk_index": 0,
      "page_number": 1,
      "chunk_text": "Executive Summary: Total quarterly revenue grew by 14% year-over-year..."
    }
  ]
  ```
- **Error Responses:**
  - `404 Not Found`: Document not found or unauthorized.

---

### 2.5 Delete Document
Deletes a document, cascades to all chunks, and deletes the binary from Supabase Storage.

- **Method:** `DELETE`
- **Route:** `/api/documents/{doc_id}`
- **Auth Required:** Yes (`Bearer <token>`)
- **Success Response (`200 OK`):**
  ```json
  {
    "message": "Document deleted successfully"
  }
  ```
- **Error Responses:**
  - `404 Not Found`: Document not found or unauthorized.

---

## 3. Query & RAG Endpoints

### 3.1 Synchronous Ask Endpoint
Executes vector retrieval and returns a fully generated answer with citations.

- **Method:** `POST`
- **Route:** `/api/query/ask`
- **Auth Required:** Yes (`Bearer <token>`)
- **Rate Limit:** 60 requests / minute
- **Request Body:**
  ```json
  {
    "question": "What was the total revenue growth in Q3?",
    "document_ids": ["9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"]
  }
  ```
  *(Note: `document_ids` is optional. If omitted, search spans all user documents).*
- **Success Response (`200 OK`):**
  ```json
  {
    "question_id": "8f3b2c1a-5d4e-4f6a-9b0c-1d2e3f4a5b6c",
    "answer": "According to the Q3 report, total revenue grew by 14% year-over-year [Doc: quarterly_earnings.pdf, Page 1].",
    "latency_ms": 482,
    "sources": [
      {
        "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "filename": "quarterly_earnings.pdf",
        "page_number": 1,
        "similarity": 0.88,
        "excerpt": "Executive Summary: Total quarterly revenue grew by 14% year-over-year..."
      }
    ]
  }
  ```

---

### 3.2 Real-Time SSE Streaming Ask Endpoint
Streams generated answer tokens and citations in real time via Server-Sent Events.

- **Method:** `GET`
- **Route:** `/api/query/ask/stream`
- **Auth Required:** Yes (via `token` query parameter or `Authorization: Bearer <token>`)
- **Query Parameters:**
  - `q` (required): Natural language question.
  - `doc_ids` (optional): Comma-separated list of document UUIDs.
  - `token` (optional if header present): JWT access token.
- **Protocol:** `text/event-stream`

#### Event Sequence Specification:
1. **`sources` Event:** Dispatched immediately once vector search completes:
   ```
   event: sources
   data: [{"filename": "quarterly_earnings.pdf", "page_number": 1, "similarity": 0.88}]
   ```
2. **`token` Event:** Dispatched repeatedly as tokens arrive from Groq LLM:
   ```
   event: token
   data: {"delta": "According "}

   event: token
   data: {"delta": "to "}

   event: token
   data: {"delta": "the "}
   ```
3. **`done` Event:** Dispatched upon completion:
   ```
   event: done
   data: {"question_id": "8f3b2c1a-5d4e-4f6a-9b0c-1d2e3f4a5b6c", "latency_ms": 512}
   ```
4. **`error` Event (on exception):**
   ```
   event: error
   data: {"detail": "Rate limit exceeded"}
   ```

---

## 4. History & Feedback Endpoints

### 4.1 Get Search History
Lists recent search queries and answers for the active user.

- **Method:** `GET`
- **Route:** `/api/history/`
- **Auth Required:** Yes (`Bearer <token>`)
- **Success Response (`200 OK`):**
  ```json
  [
    {
      "id": "8f3b2c1a-5d4e-4f6a-9b0c-1d2e3f4a5b6c",
      "query_text": "What was the total revenue growth in Q3?",
      "answer_text": "Total revenue grew by 14% year-over-year...",
      "latency_ms": 482,
      "created_at": "2026-11-27T10:10:00.000Z",
      "feedback": {
        "is_positive": true
      }
    }
  ]
  ```

---

### 4.2 Submit Answer Feedback
Submits a user rating (thumbs up or thumbs down) for a specific answer.

- **Method:** `POST`
- **Route:** `/api/history/feedback`
- **Auth Required:** Yes (`Bearer <token>`)
- **Request Body:**
  ```json
  {
    "question_id": "8f3b2c1a-5d4e-4f6a-9b0c-1d2e3f4a5b6c",
    "is_positive": true,
    "comment": "Accurate and clear citation."
  }
  ```
- **Success Response (`200 OK`):**
  ```json
  {
    "message": "Feedback submitted successfully"
  }
  ```

---

## 5. Administration & Evaluation Endpoints

### 5.1 Platform Performance Metrics
Returns aggregate platform statistics.

- **Method:** `GET`
- **Route:** `/api/admin/metrics`
- **Auth Required:** Yes (`Bearer <token>`, `role=admin`)
- **Success Response (`200 OK`):**
  ```json
  {
    "total_users": 142,
    "total_documents": 890,
    "total_chunks": 24500,
    "total_queries": 15200,
    "mean_latency_ms": 612.4,
    "satisfaction_rate": 0.94
  }
  ```

---

### 5.2 Run Benchmark Evaluation
Triggers automated evaluation against ground truth questions.

- **Method:** `POST`
- **Route:** `/api/admin/evaluate`
- **Auth Required:** Yes (`Bearer <token>`, `role=admin`)
- **Success Response (`200 OK`):**
  ```json
  {
    "run_id": "e2b3c4d5-6a7b-8c9d-0e1f-2a3b4c5d6e7f",
    "hit_rate": 0.96,
    "faithfulness": 0.98,
    "mean_latency_ms": 520.1,
    "completed_at": "2026-11-27T10:15:00.000Z"
  }
  ```

---

### 5.3 Health Check & Keep-Alive Ping
Validates backend availability and database connectivity.

- **Method:** `GET`
- **Route:** `/api/health`
- **Auth Required:** No
- **Success Response (`200 OK`):**
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected"
  }
  ```
