# SearchLab.AI – Backend & Database Guide
**Author:** Nandhishwar Reddy G (Backend + Database — 24EG510E02)  
**Date:** November 25, 2026  
**Reference Document:** `docs/API.md` (contract source of truth), `prototype/index.html`

---

## 1. Role Overview & Ownership

| Area | You Own (Nandhishwar) | Others Own |
| :--- | :--- | :--- |
| **API** | All FastAPI endpoints in `docs/API.md`, auth, input validation, error handling | Akshit (Frontend) calls them from React |
| **Database** | Supabase schema, pgvector extension, Supabase Storage buckets, migrations | — |
| **RAG Pipeline** | Document parsing (PDF, DOCX, TXT), chunking, embeddings, pgvector retrieval, fallback "not found" logic, LLM answer synthesis, citations, conflict detection | — |
| **Evaluation** | Test set runner and `/admin/evaluation/run` metrics endpoint | Sindhuja (QA) writes test question set |
| **Deployment** | Backend containerization / configuration on Render with env vars | Srikruthika (DevOps) sets up Render, Vercel, CI |
| **Testing** | Unit and integration tests for backend services | Sindhuja (QA) owns end-to-end API, UI & accuracy testing |

---

## 2. System Architecture & Information Flows

### A. Document Ingestion Flow
1. **Frontend:** Sends file (PDF, DOCX, TXT max 10MB) to `POST /documents`.
2. **Backend:** 
   - Validates file type and size.
   - Uploads raw file to Supabase Storage private bucket `documents`.
   - Inserts row in `documents` table with `status = 'processing'`.
   - Returns `202 Accepted` immediately with the document metadata.
3. **Background Worker:**
   - Extracts text page-by-page (PDF: `pypdf`) or paragraph-by-paragraph (DOCX: `python-docx`, TXT: UTF-8).
   - Validates extracted text (>20 chars, otherwise marks as failed scan).
   - Splits into chunks (150–300 words, sentence-boundary aware, 1–2 sentence overlap, preserving numbers/time formats).
   - Generates 384-dimensional dense vectors using `fastembed` (`all-MiniLM-L6-v2`).
   - Batches inserts into PostgreSQL `chunks` table.
   - Updates document status to `ready` (or `failed` with descriptive error).
4. **Frontend:** Polls `GET /documents` every 2–3s until status transitions.

### B. Query & RAG Retrieval Flow
1. **Frontend:** Sends user question to `POST /ask` with optional `document_ids` filter.
2. **Backend:**
   - Computes question embedding using `fastembed` (same model loaded once at startup).
   - Queries `chunks` using pgvector cosine distance `<=>` filtered by `user_id`, document readiness, and document selection:
     ```sql
     select c.id, c.text, c.chunk_index, d.name,
            1 - (c.embedding <=> $1) as score
     from chunks c join documents d on d.id = c.document_id
     where c.user_id = $2 and d.status = 'ready'
       and ($3::uuid[] is null or c.document_id = any($3))
     order by c.embedding <=> $1
     limit 5;
     ```
3. **Threshold Check (`RELEVANCE_THRESHOLD=0.4`):**
   - If highest score < threshold: Return `found: false` with top 2 closest chunks and **do not call LLM**.
4. **Answer Generation (Groq Llama 3):**
   - Constructs strict prompt instructing LLM to answer ONLY from supplied numbered passages `[1], [2]` and return `NOT_FOUND` if unanswerable.
   - If LLM returns `NOT_FOUND`, treat as not found.
5. **Streaming & Evidence:**
   - Stream Server-Sent Events (`event: sources`, `event: token`, `event: done`).
   - Compute evidence sentence per source (sentence most similar to answer).
   - Run conflict detection (pairwise comparison of passages across different documents for numeric disagreements with >=30% word overlap).
   - Persist question, answer, sources, and search metadata to `questions` table.

---

## 3. Technology Stack

- **Framework:** FastAPI (Python 3.11) — Async, OpenAPI docs at `/docs`, native SSE.
- **Database:** Supabase PostgreSQL with `pgvector` extension.
- **Storage:** Supabase Storage (private bucket `documents`).
- **Embeddings:** `fastembed` with `all-MiniLM-L6-v2` or `BAAI/bge-small-en-v1.5` (384 dimensions, ONNX runtime, fits Render 512MB RAM).
- **LLM:** Groq API (`llama-3.1-8b-instant` or Llama 3).
- **Text Extraction:** `pypdf` (PDF), `python-docx` (DOCX), built-in UTF-8 decoding (TXT).
- **Authentication:** JWT (`python-jose`) + password hashing (`passlib[bcrypt]`).
- **ORM / DB Driver:** `asyncpg` or `SQLAlchemy 2.0` (async).

---

## 4. Database Schema (8 Tables)

```sql
create extension if not exists vector;

-- 1. Users
create table users (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text unique not null,
  password_hash text not null,
  role text not null default 'user' check (role in ('user','admin')),
  active boolean not null default true,
  created_at timestamptz default now(),
  last_active_at timestamptz
);

-- 2. Documents
create table documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  name text not null,
  type text not null,
  size_bytes int,
  storage_path text,
  status text not null default 'processing',
  error text,
  uploaded_at timestamptz default now()
);

-- 3. Chunks (Vectors)
create table chunks (
  id bigserial primary key,
  document_id uuid references documents(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,
  chunk_index int not null,
  text text not null,
  embedding vector(384) not null
);
create index on chunks using hnsw (embedding vector_cosine_ops);

-- 4. Questions (History)
create table questions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  question text not null,
  answer text,
  found boolean not null,
  sources jsonb,
  search_info jsonb,
  asked_at timestamptz default now()
);

-- 5. Feedback
create table feedback (
  id bigserial primary key,
  question_id uuid unique references questions(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,
  helpful boolean not null,
  created_at timestamptz default now()
);

-- 6. Conflicts
create table conflicts (
  id bigserial primary key,
  doc_a text not null,
  doc_b text not null,
  text_a text not null,
  text_b text not null,
  example_question text not null,
  count int default 1,
  last_seen_at timestamptz default now()
);

-- 7. Eval Questions
create table eval_questions (
  id bigserial primary key,
  question text not null,
  expected_document text -- null = should be not found
);

-- 8. Eval Runs
create table eval_runs (
  id bigserial primary key,
  status text not null,
  metrics jsonb,
  results jsonb,
  started_at timestamptz default now(),
  finished_at timestamptz
);
```

---

## 5. API Endpoints & Priority Matrix

| Priority | Method & Path | Description | Access |
| :--- | :--- | :--- | :--- |
| **Must** | `GET /health` | Uptime check & Render wake-up | Public |
| **Must** | `POST /auth/register` | User signup & JWT issuance | Public |
| **Must** | `POST /auth/login` | User login & JWT issuance | Public |
| **Must** | `GET /auth/me` | Fetch active user session | Authenticated |
| **Must** | `GET /documents` | List caller's documents | Authenticated |
| **Must** | `POST /documents` | Upload document (multipart, background ingest) | Authenticated |
| **Must** | `DELETE /documents/{id}` | Delete document, file, chunks, vectors | Document Owner |
| **Must** | `POST /ask` | RAG query with Server-Sent Events stream | Authenticated |
| **Must** | `GET /history` | List question history (search via `?q=`) | Authenticated |
| **Must** | `GET /history/{id}` | Reopen specific answer | Question Owner |
| **Should**| `DELETE /history` | Clear user's history | Authenticated |
| **Should**| `POST /feedback` | Submit thumbs up/down | Authenticated |
| **Should**| `POST /documents/text` | Create doc from raw pasted text | Authenticated |
| **Should**| `POST /admin/evaluation/run` | Trigger evaluation benchmark | Admin only |
| **Should**| `GET /admin/evaluation/runs/{id}` | Fetch eval benchmark results | Admin only |
| **Should**| `GET /admin/users` | List all users | Admin only |
| **Should**| `POST /admin/users/invite` | Invite new user | Admin only |
| **Should**| `PATCH /admin/users/{id}` | Update role / deactivate user | Admin only |
| **Could** | `GET /admin/gaps` | Unanswered questions & conflicts list | Admin only |

---

## 6. Implementation Roadmap by Phase

1. **Phase 1: Foundation**
   - Create Supabase project, enable `pgvector`, execute table creation SQL.
   - Create private storage bucket `documents`.
   - Setup `backend/` directory in repo with `app/main.py`, `requirements.txt`, `.env.example`.
   - Implement `GET /health` with CORS configured for `http://localhost:5173` and production Vercel domain.
2. **Phase 2: Auth**
   - User registration and login with bcrypt hashing and JWT tokens.
   - Implement `get_current_user` and `require_admin` FastAPI dependencies.
   - Seed an admin account for evaluation/testing.
3. **Phase 3: Documents & Ingestion**
   - File upload validation (type, size <= 10MB) & upload to Supabase Storage.
   - Background processing worker: `pypdf`/`python-docx` text extraction -> chunking -> `fastembed` -> `chunks` storage.
   - Status updates (`processing` -> `ready` / `failed`).
   - Document listing and cascading deletion.
4. **Phase 4: RAG & Ask**
   - Embed question using `fastembed`.
   - Query `chunks` via pgvector cosine distance, applying relevance threshold (0.4).
   - Strict Groq Llama 3 generation with citations `[1]`, `[2]`.
   - Server-Sent Events (SSE) streaming (`sources`, `token`, `done`).
   - Evidence sentence extraction and conflict detection.
5. **Phase 5: History, Feedback & Admin**
   - Question history persistence, search, reopen, and clear.
   - Feedback rating (`helpful`).
   - Evaluation benchmark runner against test set.
   - Admin user management and coverage gaps summary.
6. **Phase 6: Deployment & Production Readiness**
   - Render deployment verification (RAM < 512MB, cold-start handling).
   - Environment variables management.
   - Write `backend/README.md`.
