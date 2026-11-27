-- SearchLab.AI Initial Schema Migration
-- Enables pgvector and establishes core entities

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  last_active_at TIMESTAMPTZ
);

-- 3. Documents Table
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  size_bytes INT,
  storage_path TEXT,
  status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'failed')),
  error TEXT,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- Index for user documents lookup
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);

-- 4. Chunks Table (384-dimensional vector for MiniLM / BGE-small)
CREATE TABLE IF NOT EXISTS chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  text TEXT NOT NULL,
  embedding VECTOR(384) NOT NULL
);

-- HNSW Cosine Index for ultra-fast approximate nearest neighbor vector search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_chunks_user_doc ON chunks (user_id, document_id);

-- 5. Questions / History Table
CREATE TABLE IF NOT EXISTS questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  answer TEXT,
  found BOOLEAN NOT NULL,
  sources JSONB DEFAULT '[]'::jsonb,
  search_info JSONB DEFAULT '{}'::jsonb,
  asked_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_user_asked ON questions(user_id, asked_at DESC);

-- 6. Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
  id BIGSERIAL PRIMARY KEY,
  question_id UUID UNIQUE NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  helpful BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 7. Conflicts Table ("Sources disagree")
CREATE TABLE IF NOT EXISTS conflicts (
  id BIGSERIAL PRIMARY KEY,
  doc_a TEXT NOT NULL,
  doc_b TEXT NOT NULL,
  text_a TEXT NOT NULL,
  text_b TEXT NOT NULL,
  example_question TEXT NOT NULL,
  count INT DEFAULT 1,
  last_seen_at TIMESTAMPTZ DEFAULT now()
);

-- 8. Eval Questions (Benchmark ground truth)
CREATE TABLE IF NOT EXISTS eval_questions (
  id BIGSERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  expected_document TEXT -- NULL indicates this question is out-of-scope and should be 'not found'
);

-- 9. Eval Runs (Benchmark metrics store)
CREATE TABLE IF NOT EXISTS eval_runs (
  id BIGSERIAL PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'running',
  metrics JSONB DEFAULT '{}'::jsonb,
  results JSONB DEFAULT '[]'::jsonb,
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ
);
