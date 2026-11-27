# SearchLab.AI Backend

FastAPI backend for SearchLab.AI semantic search with cited answers.

## Architecture & Capabilities

- **Auth**: JWT tokens, bcrypt password hashing, role-based access (`user` and `admin`).
- **Documents**: File uploads (PDF, DOCX, TXT) with automatic page-by-page / paragraph text extraction, 150-300 word chunking with 1-2 sentence overlap, and Supabase Storage persistence.
- **RAG Engine**:
  - `fastembed` (`BAAI/bge-small-en-v1.5`, 384-dim dense vectors).
  - Supabase `pgvector` HNSW cosine similarity search with user-isolation filter.
  - Relevance gating (`RELEVANCE_THRESHOLD=0.4`): strictly responds with "This isn't in your documents." if no relevant match is found.
  - Groq API (`llama-3.1-8b-instant`) with strict grounded citations `[1]`, `[2]`.
  - Server-Sent Events (SSE) streaming (`sources` -> `token` -> `done`).
  - Source disagreement / conflict detection.
- **Admin**: User roles, invites, deactivation, evaluation benchmark runner, and coverage gaps tracking.

## Running the Backend

```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (one-time)
python run_migration.py

# Seed demo accounts (admin@demo.com / admin1234, user@demo.com / user1234)
python seed_admin.py

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation available at: **http://localhost:8000/docs**
