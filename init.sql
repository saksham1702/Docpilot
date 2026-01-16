-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the chunks table
CREATE TABLE IF NOT EXISTS doc_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    url TEXT,
    library_name TEXT,
    version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding vector(384) 
);

-- Note: IVFFlat index requires 100+ rows to be effective
-- Add this later: CREATE INDEX ON doc_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

