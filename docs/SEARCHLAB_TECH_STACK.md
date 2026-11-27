# SEARCHLAB.AI — COMPLETE TECHNOLOGY STACK INVENTORY

**Document Version:** 1.0.0  
**Verification Method:** Direct Codebase, Package Manifests & Dependency Tree Analysis  

---

## 1. Complete Technology Inventory Matrix

| Domain | Technology / Package | Specific Version | Purpose in SearchLab.AI | Implementation Status |
|---|---|---|---|---|
| **Frontend Framework** | React | 18.3.1 | Core UI view layer and component rendering | FULLY IMPLEMENTED |
| **Frontend Runtime** | React DOM | 18.3.1 | DOM manipulation and web mounting | FULLY IMPLEMENTED |
| **Build Tooling** | Vite | 5.4.21 | Bundler, ESM module server, and asset optimization | FULLY IMPLEMENTED |
| **CSS Styling** | Tailwind CSS | 3.4.1 | Utility-first responsive styling and typography | FULLY IMPLEMENTED |
| **CSS Preprocessor** | PostCSS & Autoprefixer | 8.4.35 / 10.4.18 | Vendor prefixing and stylesheet compilation | FULLY IMPLEMENTED |
| **Client Routing** | React Router DOM | 6.22.3 | Declarative SPA client-side routing | FULLY IMPLEMENTED |
| **Iconography** | Lucide React | 0.344.0 | UI icons (search, document, upload, lock, etc.) | FULLY IMPLEMENTED |
| **Markdown Parser** | React Markdown | 9.0.1 | Renders markdown-formatted LLM answer text | FULLY IMPLEMENTED |
| **Backend Framework** | FastAPI | 0.110.0+ | Modern async Python REST & SSE web API framework | FULLY IMPLEMENTED |
| **ASGI Server** | Uvicorn | 0.28.0+ | Production ASGI server with multi-worker support | FULLY IMPLEMENTED |
| **Data Validation** | Pydantic & Pydantic-Settings | 2.6.4+ / 2.2.1+ | Schema serialization, validation & env parsing | FULLY IMPLEMENTED |
| **Relational Database** | PostgreSQL via Supabase | 15.x | Relational ACID transactional storage | FULLY IMPLEMENTED |
| **Vector Engine** | pgvector PostgreSQL Extension | 0.5.0+ | High-dimensional dense vector storage & search | FULLY IMPLEMENTED |
| **PostgreSQL Driver** | psycopg2-binary | 2.9.9+ | Threaded connection pooling and SQL queries | FULLY IMPLEMENTED |
| **File Object Storage** | Supabase Storage Bucket | Bucket: `documents` | Private, secure binary document storage | FULLY IMPLEMENTED |
| **Storage API Client** | HTTPX | 0.27.0+ | Async HTTP client for Supabase Storage REST API | FULLY IMPLEMENTED |
| **Embedding Engine** | FastEmbed (Qdrant) | 0.2.6+ | Local in-process dense vector generation | FULLY IMPLEMENTED |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` | 384-dimensional | Text representation vector model | FULLY IMPLEMENTED |
| **LLM Provider** | Groq Cloud API | Groq SDK 0.5.0+ | Ultra-fast inference engine for grounded answers | FULLY IMPLEMENTED |
| **LLM Model** | `openai/gpt-oss-120b` | Cloud endpoint | Primary model for natural language generation | FULLY IMPLEMENTED |
| **PDF Extraction** | PyMuPDF (`fitz`) | 1.23.26+ | Fast, page-aware text and metadata extraction | FULLY IMPLEMENTED |
| **DOCX Extraction** | `python-docx` | 1.1.0+ | Word document paragraph and table extraction | FULLY IMPLEMENTED |
| **Authentication & Crypto**| `python-jose` (cryptography) | 3.3.0+ | JWT token generation and validation (HS256) | FULLY IMPLEMENTED |
| **Password Hashing** | `passlib` (bcrypt) | 1.7.4+ / 4.0.1+ | Cryptographic salted password hashing | FULLY IMPLEMENTED |
| **Multipart Parsing** | `python-multipart` | 0.0.9+ | Form-data and binary document upload streaming | FULLY IMPLEMENTED |
| **Streaming Protocol** | Server-Sent Events (SSE) | W3C Standard | Streaming token delivery and citation events | FULLY IMPLEMENTED |
| **Backend Deployment** | Render | Docker/Python 3.12 | Containerized Web Service | DEPLOYMENT READY |
| **Frontend Deployment** | Vercel | Global Edge CDN | Fast static SPA hosting | DEPLOYMENT READY |
| **CI/CD** | GitHub Actions | Modern Runners | Automated linting, test suites, and deployments | CONFIGURED |

---

## 2. Frontend Manifest Breakdown (`frontend/package.json`)

```json
{
  "dependencies": {
    "clsx": "^2.1.0",
    "lucide-react": "^0.344.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1",
    "react-router-dom": "^6.22.3",
    "tailwind-merge": "^2.2.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.56",
    "@types/react-dom": "^18.2.19",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.18",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.1",
    "vite": "^5.4.21"
  }
}
```

---

## 3. Backend Manifest Breakdown (`backend/requirements.txt`)

```
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.4
pydantic-settings>=2.2.1
psycopg2-binary>=2.9.9
fastembed>=0.2.6
groq>=0.5.0
pymupdf>=1.23.26
python-docx>=1.1.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.0.1
python-multipart>=0.0.9
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.5
```
