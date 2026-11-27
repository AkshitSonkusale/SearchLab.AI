# SEARCHLAB.AI — SYSTEM ARCHITECTURE SPECIFICATION

**Document Version:** 1.0.0  
**Target Audience:** Architects, Lead Developers, DevOps & Security Engineers  
**System Type:** Multi-Tenant Semantic Search & Document Intelligence Platform  

---

## 1. High-Level Modular Architecture

SearchLab.AI is structured into six discrete, loosely coupled modules conforming to the Team 17 Architecture Blueprint:

```mermaid
graph TD
    subgraph Frontend_FE ["01. Frontend (FE) - React SPA (Vercel)"]
        UI_Auth["Sign In & Accounts<br>(Login / Register)"]
        UI_Ask["Ask & Query Bar<br>(Search / Filter)"]
        UI_Answer["Answer View<br>(SSE Streaming & Citations)"]
        UI_Docs["Document Manager<br>(Upload / Status / Delete)"]
        UI_Admin["Admin Dashboard<br>(Metrics & Evaluations)"]
    end

    subgraph Backend_BE ["02. Backend (BE) - FastAPI (Render)"]
        API_Auth["Auth Service<br>(JWT, RBAC, Blacklist)"]
        API_Docs["Document API<br>(Upload & CRUD)"]
        API_Query["Query API<br>(Ask & SSE Stream)"]
        API_History["History API<br>(Logs & Feedback)"]
        API_Eval["Evaluation API<br>(Automated Benchmarks)"]
    end

    subgraph RAG_AI ["03. RAG / AI Pipeline (Python)"]
        P_Extract["Text Extraction<br>(PyMuPDF / python-docx)"]
        P_Chunk["Semantic Chunking<br>(Sentence-aware 150-300w)"]
        P_Embed["FastEmbed Engine<br>(BAAI/bge-small-en-v1.5)"]
        P_Search["pgvector Cosine Search<br>(Top-K = 5, Thresh >= 0.50)"]
        P_LLM["LLM Grounded Synthesis<br>(Groq openai/gpt-oss-120b)"]
    end

    subgraph Database_Storage ["04. Database & Storage (Supabase)"]
        DB_Postgres[("Supabase PostgreSQL<br>Users, Docs, History")]
        DB_Vectors[("pgvector Extension<br>HNSW 384-dim Index")]
        ST_Files["Supabase Storage<br>Bucket: documents"]
        DB_Eval[("Evaluation Store<br>Questions & Benchmark Runs")]
    end

    subgraph DevOps_Deployment ["05. DevOps & Infrastructure"]
        GH["GitHub Repository"]
        GA["GitHub Actions CI"]
        Vercel["Vercel Edge Network (FE)"]
        Render["Render Web Service (BE)"]
        Ping["Uptime Monitor / Health Ping"]
    end

    %% Communication links
    Frontend_FE -->|"HTTPS REST + SSE Streaming"| Backend_BE
    Backend_BE -->|"Service Orchestration"| RAG_AI
    RAG_AI -->|"SQL & Vector Queries"| Database_Storage
    API_Docs -->|"S3 REST API"| ST_Files
    GH -->|"Continuous Deployment"| GA
    GA --> Vercel
    GA --> Render
    Ping -.->|"Health Checks (/api/health)"| Render
```

---

## 2. End-to-End Component Sequence Interaction

The sequence diagram below illustrates the exact request-response lifecycle across the browser, application server, Supabase, FastEmbed, and Groq Cloud:

```mermaid
sequenceDiagram
    autonumber
    actor User as Knowledge Worker (Browser)
    participant FE as React SPA (Vercel)
    participant BE as FastAPI Backend (Render)
    participant FastEmbed as FastEmbed (Local ONNX)
    participant Supabase as Supabase (Postgres + pgvector)
    participant Groq as Groq Cloud API (gpt-oss-120b)

    %% Authentication Flow
    Note over User, BE: 1. Authentication Lifecycle
    User->>FE: Enter Email & Password
    FE->>BE: POST /api/auth/login {email, password}
    BE->>Supabase: SELECT * FROM users WHERE email = ?
    Supabase-->>BE: User Record (bcrypt hash)
    BE->>BE: Verify Bcrypt Hash & Generate JWT
    BE-->>FE: 200 OK {access_token, token_type, role}
    FE->>FE: Store JWT in localStorage

    %% Document Ingestion Flow
    Note over User, Supabase: 2. Document Ingestion Lifecycle
    User->>FE: Drag & Drop PDF Document
    FE->>BE: POST /api/documents/upload (Multipart Form + JWT)
    BE->>BE: Validate Magic Bytes (%PDF-) & File Size (<25MB)
    BE->>Supabase: Upload binary to Storage Bucket 'documents'
    BE->>Supabase: INSERT INTO documents (status='pending')
    BE->>BE: Extract text via PyMuPDF page-by-page
    BE->>BE: Chunk text (150-300 words with sentence overlap)
    BE->>FastEmbed: Generate 384-dim embeddings for all chunks
    FastEmbed-->>BE: Dense Vector Arrays
    BE->>Supabase: Batch INSERT INTO chunks (document_id, text, page, embedding)
    BE->>Supabase: UPDATE documents SET status='processed', chunk_count=N
    BE-->>FE: 201 Created {document_id, status: 'processed'}

    %% Query & Answer Flow
    Note over User, Groq: 3. Semantic Retrieval & Grounded Answer Flow
    User->>FE: Enter Query: "What were Q3 revenue numbers?"
    FE->>BE: GET /api/query/ask/stream?q=... (SSE with JWT)
    BE->>FastEmbed: Embed Query String
    FastEmbed-->>BE: Query Embedding Vector (384-dim)
    BE->>Supabase: Query chunks WHERE user_id = ? ORDER BY embedding <=> query_vec ASC LIMIT 5
    Supabase-->>BE: Top 5 Relevant Chunks (Cosine Similarity >= 0.50)
    BE->>BE: Build Grounded Prompt with Citations & Anti-Hallucination Guardrails
    BE-->>FE: SSE Event: 'sources' [{file, page, text}]
    BE->>Groq: Stream Completion (temperature=0.1, max_tokens=800)
    loop Token Streaming
        Groq-->>BE: Streaming LLM Token
        BE-->>FE: SSE Event: 'token' {delta: "..."}
        FE->>User: Real-time Markdown Render
    end
    Groq-->>BE: [Done]
    BE->>Supabase: INSERT INTO questions (query, answer, latency_ms, chunk_ids)
    BE-->>FE: SSE Event: 'done' {question_id, latency_ms}
```

---

## 3. RAG Pipeline Execution Architecture

```mermaid
flowchart TD
    Q[User Natural Language Query] --> EMB[FastEmbed Local Embedding Generation<br>Model: BAAI/bge-small-en-v1.5]
    EMB --> VEC[384-Dimensional Dense Vector]
    
    VEC --> HNSW[Supabase pgvector HNSW Index Scan<br>Cosine Distance: 1 - embedding <=> query_vec]
    
    subgraph Multi_Tenant_Filter ["Strict Tenant Isolation Boundary"]
        HNSW --> FILTER["Filter WHERE user_id = current_user.id<br>AND document_id IN (optional filter)"]
    end
    
    FILTER --> RANK[Ranked Candidate Chunks]
    
    RANK --> THRESH{Cosine Similarity >= 0.50?}
    THRESH -- No --> REJECT[Discard Chunk]
    THRESH -- Yes --> PASS[Retain Top-5 Context Chunks]
    
    PASS --> CTX_CHECK{Candidate Count > 0?}
    CTX_CHECK -- No --> NO_DATA["Return Grounded Fallback:<br>'I could not find the answer in uploaded documents.'"]
    
    CTX_CHECK -- Yes --> PROMPT["Construct Grounded Prompt:<br>- Enforce Strict Context Constraint<br>- Inject Bracketed Document & Page Citations<br>- Neutralize System Override Instructions"]
    
    PROMPT --> GROQ[Groq Cloud LLM Engine<br>Model: openai/gpt-oss-120b<br>Temperature: 0.1 | Max Tokens: 800]
    
    GROQ --> STREAM[FastAPI Server-Sent Events (SSE) Stream]
    STREAM --> CLIENT[React UI: Live Token Typing & Citation Badges]
```

---

## 4. Network Topology & Deployment Boundaries

```mermaid
graph LR
    subgraph Public_Internet ["Public Internet"]
        Client["Browser Client<br>HTTPS / TLS 1.3"]
    end

    subgraph Edge_Network ["Edge Network (Vercel)"]
        Vercel_CDN["Vercel Global Edge CDN<br>Static React SPA"]
    end

    subgraph Application_Cloud ["Cloud Application Service (Render)"]
        FastAPI_App["FastAPI ASGI App<br>Dockerized Container<br>Port 8000"]
        FastEmbed_Engine["FastEmbed Runtime<br>In-Process ONNX Engine"]
    end

    subgraph External_SaaS ["External Enterprise SaaS Tier"]
        Supabase_DB["Supabase Managed PostgreSQL 15<br>pgvector Extension"]
        Supabase_S3["Supabase Private Storage<br>Bucket: documents"]
        Groq_API["Groq Cloud API<br>Inference Processing"]
    end

    Client -->|"HTTPS / Port 443"| Vercel_CDN
    Client -->|"HTTPS / Port 443 (REST + SSE)"| FastAPI_App
    FastAPI_App -->|"In-Memory IPC"| FastEmbed_Engine
    FastAPI_App -->|"TLS Encrypted PostgreSQL (Port 5432)"| Supabase_DB
    FastAPI_App -->|"HTTPS / REST API"| Supabase_S3
    FastAPI_App -->|"HTTPS / REST API"| Groq_API
```
