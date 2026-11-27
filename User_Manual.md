# SearchLab.AI — Complete User Manual & Online Deployment Guide

Welcome to the **SearchLab.AI** step-by-step user manual. This guide will walk you through everything from cloning the GitHub repository to configuring free cloud services and deploying your frontend, backend, database, and storage completely online.

---

## Architecture Overview for Online Deployment

```
[ Frontend: React SPA ]   --->   [ Backend: FastAPI ]   --->   [ Cloud Services ]
  Hosted on: Vercel               Hosted on: Render              - Database: Supabase PostgreSQL + pgvector
  URL: https://...vercel.app      URL: https://...onrender.com   - Storage: Supabase Storage Bucket ('documents')
                                                                 - LLM: Groq Cloud API (gpt-oss-120b)
```

---

## 1. Prerequisites (Accounts You Need)

Before deploying, create free accounts on these platforms (no credit card required for standard tiers):

1. **GitHub:** [https://github.com](https://github.com) (stores your source code).
2. **Supabase:** [https://supabase.com](https://supabase.com) (manages your PostgreSQL database, pgvector, and file storage).
3. **Groq Cloud:** [https://console.groq.com](https://console.groq.com) (fast AI model inference).
4. **Render:** [https://render.com](https://render.com) (hosts the Python FastAPI backend).
5. **Vercel:** [https://vercel.com](https://vercel.com) (hosts the React frontend).

---

## 2. Step 1: Clone the GitHub Repository

Open your terminal or command prompt:

```bash
git clone https://github.com/AkshitSonkusale/SearchLab.AI.git
cd SearchLab.AI
```

If you want to deploy from your own GitHub account:
1. Fork the repository to your own GitHub profile on [GitHub](https://github.com/AkshitSonkusale/SearchLab.AI).
2. Clone your personal fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/SearchLab.AI.git
   cd SearchLab.AI
   ```

---

## 3. Step 2: Set Up Supabase (Database & Storage)

### A. Create a New Project
1. Log in to [Supabase](https://supabase.com/dashboard).
2. Click **New Project**.
3. Choose a name (e.g. `SearchLab-AI`), set a strong database password, and choose your preferred region.
4. Click **Create new project** and wait 1–2 minutes for provisioning.

### B. Enable `pgvector` & Apply Database Schema
1. In your Supabase Dashboard, click on **SQL Editor** (the terminal icon on the left menu).
2. Click **New Query**.
3. Copy the entire contents of the migration script from your repository:
   - File location: `backend/migrations/001_initial_schema.sql`
4. Paste it into the SQL Editor and click **Run**.
5. You should see `Success. No rows returned`. This creates:
   - The `vector` extension.
   - Tables: `users`, `documents`, `chunks`, `questions`, `feedback`, `conflicts`, `eval_questions`, `eval_runs`.
   - The HNSW vector cosine search index.

### C. Create Private Storage Bucket
1. In the Supabase Dashboard left menu, click **Storage**.
2. Click **New Bucket**.
3. Name the bucket exactly: `documents`.
4. Leave **Public Bucket** turned **OFF** (this ensures user documents stay private).
5. Click **Save**.

### D. Collect Your Supabase Credentials
Go to **Project Settings** (gear icon) -> **API**:
- **Project URL:** `https://your-project-id.supabase.co`
- **Project API Keys -> `service_role` (secret):** Click reveal and copy this key. *(Keep this private — it allows backend file uploads)*.

Go to **Project Settings** -> **Database**:
- Under **Connection string**, select **URI**.
- Copy the connection URI:
  ```
  postgresql://postgres:[YOUR-PASSWORD]@db.your-project-id.supabase.co:5432/postgres
  ```
  *(Replace `[YOUR-PASSWORD]` with your real database password).*

---

## 4. Step 3: Get Groq API Key

1. Log in to [Groq Console](https://console.groq.com/keys).
2. Click **Create API Key**.
3. Name it `SearchLab-AI`.
4. Copy the generated API key (it begins with `gsk_...`).

---

## 5. Step 4: Deploy Backend on Render

The backend is built with FastAPI and runs directly on Render.

1. Log in to [Render](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository (`SearchLab.AI`).
4. Configure the service settings:
   - **Name:** `searchlab-ai-backend` (or your chosen name)
   - **Region:** Choose the region closest to your Supabase project (e.g. Oregon, Frankfurt, Singapore).
   - **Branch:** `main`
   - **Root Directory:** `SearchLab.AI/backend` *(or `backend` if deploying from the root of a repo fork)*
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** `Free`

5. Scroll down to **Environment Variables** and add the following keys:

| Key | Value Example | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres` | Your Supabase pooled DB URI |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOi...` | Supabase `service_role` secret key |
| `SUPABASE_STORAGE_BUCKET` | `documents` | Private storage bucket name |
| `GROQ_API_KEY` | `gsk_...` | Your Groq Cloud API Key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Target LLM model |
| `JWT_SECRET` | `4f8b9e2d7c1a5e3f8b0a9c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7` | Any random 64-character string |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Token validity in minutes (8 hours) |
| `RELEVANCE_THRESHOLD` | `0.50` | Minimum cosine similarity |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Dense vector embedding model |
| `TOP_K_CHUNKS` | `5` | Retrieved context chunk limit |
| `APP_NAME` | `SearchLab.AI` | Application name |
| `APP_ENV` | `production` | Environment mode |
| `FRONTEND_ORIGIN` | `https://your-searchlab.vercel.app,http://localhost:5173` | Allowed CORS origins (update with Vercel URL in Step 5) |

6. Click **Deploy Web Service**.
7. Wait 2–3 minutes for the build to finish. Once live, Render will give you a public URL like:
   ```
   https://searchlab-ai-backend.onrender.com
   ```
8. **Verify the backend:** Open `https://searchlab-ai-backend.onrender.com/health` in your browser. You should see:
   ```json
   {"status":"healthy","app":"SearchLab.AI","environment":"production"}
   ```

---

## 6. Step 5: Deploy Frontend on Vercel

The frontend is a React Single Page Application (SPA) powered by Vite.

1. Log in to [Vercel](https://vercel.com/dashboard).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository (`SearchLab.AI`).
4. Configure Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click **Edit** and select `SearchLab.AI/frontend` *(or `frontend` if repo root is direct)*.
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Expand the **Environment Variables** section and add:

| Key | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://searchlab-ai-backend.onrender.com` *(your Render backend URL from Step 4)* |

6. Click **Deploy**.
7. In about 1 minute, Vercel will deploy your site and provide your live frontend URL:
   ```
   https://searchlab-ai.vercel.app
   ```

---

## 7. Step 6: Connect CORS & Final Check

1. Go back to your **Render Dashboard** -> Web Service -> **Environment**.
2. Update `FRONTEND_ORIGIN` with your real Vercel URL:
   ```
   FRONTEND_ORIGIN=https://searchlab-ai.vercel.app
   ```
3. Render will automatically redeploy with the updated CORS policy.

---

## 8. How to Use SearchLab.AI (User Guide)

Now that your application is live online, follow these steps to test and use it:

### 1. Create an Account
1. Open your Vercel URL in your browser (`https://searchlab-ai.vercel.app`).
2. Click **Register** or **Sign In**.
3. Enter your Name, Email, and a password (minimum 8 characters).
4. Click **Create account**. You will be logged in automatically.

### 2. Upload Documents
1. Go to the **Documents** tab in the sidebar.
2. Drag and drop or browse to select your files:
   - **Supported formats:** `.pdf`, `.docx`, `.txt`
   - **Maximum file size:** 25MB per file.
3. The upload status will show `processing` while the backend extracts text, creates chunks, and generates vector embeddings.
4. Once ready, the status badge turns to green: `Ready`.

### 3. Ask Questions & Get Verifiable Answers
1. Go to the **Ask** tab.
2. In the search bar, type any natural language question about your documents (e.g., *"What is the leave policy?"*, *"Summarize Q3 revenue numbers"*).
3. (Optional) Use the document dropdown to restrict your search to a specific document or search across all documents.
4. Click **Ask**:
   - The answer will stream live token-by-token from Groq.
   - Interactive source citation cards will appear on the right side showing the exact file name, page number, match percentage, and highlighted source excerpt.
   - Clickable numbers (e.g. `[1]`, `[2]`) in the answer link directly to each cited source.

### 4. Provide Feedback & Review History
- Below the answer, click **Yes** or **No** to rate the quality of the answer.
- Visit the **History** tab to see past searches, full answers, and timestamps.

### 5. Access Admin Metrics
- If your account has the `Admin` role, visit the **Admin** tab to view platform metrics (hit rate, faithfulness, average latency) and run benchmark evaluations.

---

## 9. Troubleshooting & FAQ

### Q: Why does the Render backend take ~50 seconds to respond after being idle?
- Render's free tier puts web services to sleep after 15 minutes of inactivity. The first request will wake up the instance.
- **Solution:** Set up a free uptime monitor (like [UptimeRobot](https://uptimerobot.com) or [Cron-Job.org](https://cron-job.org)) to ping `https://your-backend.onrender.com/health` every 10 minutes.

### Q: Why do I get a blank screen or CORS error?
- Ensure `FRONTEND_ORIGIN` on Render matches your exact Vercel URL (including `https://` with no trailing slash).
- Ensure `VITE_API_BASE_URL` in Vercel contains your exact Render URL with no trailing slash.

### Q: What if a document says "This isn’t in your documents"?
- SearchLab.AI enforces a strict `RELEVANCE_THRESHOLD = 0.50` to eliminate hallucinations. If your document doesn't contain information related to the question, it will state that the answer was not found rather than making up facts.
