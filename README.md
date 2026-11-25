# SearchLab.AI

Semantic search with answers. Upload documents, ask questions in plain English, and get answers with the exact passage they came from. If the answer isn't in your documents, it says so.

## What's in this repo

| Folder | What it is |
| --- | --- |
| `prototype/` | Clickable UI prototype in one HTML file: landing page, sign-in and the full app. Open `prototype/index.html` in a browser. Search runs in the browser with sample documents, so it works without a backend. |
| `frontend/` | The React + Vite + Tailwind app that will be deployed on Vercel. Uses sample data for now; each page has a comment naming the API endpoint it needs. |
| `docs/API.md` | **The API contract between frontend and backend.** Backend: start here. |
| `backend/` | *(to be added)* FastAPI app for Render. |

## Run the frontend

```bash
cd frontend
cp .env.example .env      # set VITE_API_URL to the backend URL
npm install
npm run dev               # http://localhost:5173
```

## Prototype demo logins

Any email and password work. An email containing "admin" (for example `admin@demo.com`) shows the admin pages: Evaluation, Coverage gaps and Users.

Things to try in the prototype:

- **"How many days in advance should I request leave?"**: two documents disagree, and the app shows both ("Sources disagree").
- **"What is the CEO's salary?"**: not in the documents, so it answers "This isn't in your documents" instead of guessing.
- Open **How I searched** under any answer to see how the question was interpreted and scored.
- **Coverage gaps** (admin) lists unanswered questions and conflicting documents.

## Prototype vs real app

The prototype's search is a stand-in: keyword matching with a small synonym list, and answers assembled from the best-matching sentences. The real backend uses embeddings (MiniLM), pgvector in Supabase, and Llama 3 on Groq, as described in the BRD and `docs/API.md`.

## Stack

React, Vite, Tailwind (Vercel) · FastAPI (Render) · Supabase PostgreSQL + pgvector + Storage · MiniLM embeddings · Llama 3 via Groq
