# SEARCHLAB.AI — DEPLOYMENT & OPERATIONS GUIDE

**Document Version:** 1.0.0  
**Target Environments:** Local Development, Supabase, Render (Backend), Vercel (Frontend)  
**Assigned Lead:** Srikruthika Katta (23EG107A30) — Deployment (DevOps)  

---

## 1. Local Development Setup

### 1.1 System Prerequisites
- **Python:** 3.11 or 3.12 (64-bit)
- **Node.js:** v18.x or v20.x LTS + npm
- **PostgreSQL:** Access to a Supabase project or local PostgreSQL instance with the `vector` extension enabled.

---

### 1.2 Backend Local Setup

1. **Navigate to the Backend Directory:**
   ```bash
   cd SearchLab.AI/backend
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file inside `SearchLab.AI/backend/` using the template below:
   ```env
   # Database Configuration (Supabase PostgreSQL)
   DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres

   # Supabase Storage Configuration
   SUPABASE_URL=https://[PROJECT_ID].supabase.co
   SUPABASE_SERVICE_KEY=[SUPABASE_SERVICE_ROLE_KEY]
   SUPABASE_STORAGE_BUCKET=documents

   # Groq LLM Configuration
   GROQ_API_KEY=[GROQ_API_KEY]
   GROQ_MODEL=openai/gpt-oss-120b

   # JWT Authentication Secrets
   JWT_SECRET=[RANDOM_HEX_64_CHARACTERS]
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=480

   # RAG & Embeddings
   RELEVANCE_THRESHOLD=0.50
   EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
   TOP_K_CHUNKS=5

   # Server & CORS
   APP_NAME=SearchLab.AI
   APP_ENV=development
   APP_PORT=8000
   FRONTEND_ORIGIN=http://localhost:5173
   ```

5. **Start Backend Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Verify backend health at `http://localhost:8000/api/health`.*

---

### 1.3 Frontend Local Setup

1. **Navigate to the Frontend Directory:**
   ```bash
   cd SearchLab.AI/frontend
   ```

2. **Install Node Packages:**
   ```bash
   npm install
   ```

3. **Configure Environment Variables:**
   Create `.env.local` inside `SearchLab.AI/frontend/`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

4. **Start Development Server:**
   ```bash
   npm run dev
   ```
   *Access the web application at `http://localhost:5173`.*

---

## 2. Supabase Infrastructure Configuration

### 2.1 Enable the `pgvector` Extension
Execute in the Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2.2 Apply Relational Schema Migrations
Run the complete contents of `SearchLab.AI/backend/migrations/001_initial_schema.sql` in the Supabase SQL Editor. This initializes all 8 tables, constraints, foreign keys, and the HNSW cosine index:
```sql
CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON chunks USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

### 2.3 Create Private Storage Bucket
1. Go to **Supabase Dashboard** -> **Storage**.
2. Click **New Bucket**.
3. Name the bucket `documents`.
4. Ensure **Public Bucket** is set to **OFF** (Private).
5. Save the bucket configuration.

---

## 3. Production Deployment on Render (Backend)

The backend is deployed as a Web Service on Render using the included `backend/Dockerfile` or native Python environment.

### 3.1 Web Service Setup
1. Log in to [Render](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository (`SearchLab.AI`).
4. Configure service parameters:
   - **Name:** `searchlab-backend`
   - **Root Directory:** `SearchLab.AI/backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free or Starter

### 3.2 Environment Variables on Render
Add each variable in the Render Environment settings:
- `DATABASE_URL`: Your Supabase connection string.
- `SUPABASE_URL`: `https://[PROJECT_ID].supabase.co`
- `SUPABASE_SERVICE_KEY`: `[SERVICE_ROLE_KEY]`
- `SUPABASE_STORAGE_BUCKET`: `documents`
- `GROQ_API_KEY`: `[GROQ_KEY]`
- `GROQ_MODEL`: `openai/gpt-oss-120b`
- `JWT_SECRET`: Production secret key.
- `JWT_ALGORITHM`: `HS256`
- `FRONTEND_ORIGIN`: `https://searchlab.vercel.app`

### 3.3 Health Checks & Keep-Alive Monitoring
Set the Health Check Path in Render to `/api/health`. Free tier instances sleep after 15 minutes of inactivity; set up a free monitor (e.g. UptimeRobot or Cron-Job) to ping `https://searchlab-backend.onrender.com/api/health` every 10 minutes.

---

## 4. Production Deployment on Vercel (Frontend)

The frontend is deployed to Vercel's global edge network.

### 4.1 Project Configuration
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import the `SearchLab.AI` repository.
4. Set the build parameters:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `SearchLab.AI/frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### 4.2 Environment Variables on Vercel
Add the production backend URL:
- `VITE_API_BASE_URL`: `https://searchlab-backend.onrender.com/api`

### 4.3 Single Page Application (SPA) Routing Configuration
Ensure `SearchLab.AI/frontend/vercel.json` exists to prevent 404 errors on browser refresh:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 5. Verification & Smoke Testing Protocol

After deploying both services, run the following verification steps:

1. **Verify Health Endpoint:**
   ```bash
   curl -i https://searchlab-backend.onrender.com/api/health
   # Expected: HTTP 200 OK {"status":"healthy", "database":"connected"}
   ```
2. **Execute Full Automated Test Suites:**
   ```bash
   cd SearchLab.AI/backend
   python tests/run_full_test_suite.py
   python tests/run_security_audit_suite.py
   # Expected: 27/27 functional tests PASS, 22/22 security tests PASS.
   ```
