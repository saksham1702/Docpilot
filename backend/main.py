import os
import json
import requests
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")

class QuestionRequest(BaseModel):
    question: str
    library: str = None  # Optional filter
    version: str = None  # Optional filter
    top_k: int = 3       # Number of results

class Citation(BaseModel):
    url: str
    library: str
    version: str
    snippet: str

class AnswerResponse(BaseModel):
    question: str
    citations: list[Citation]
    context: str

def get_embedding(text: str):
    """Call Modal API to get embedding vector."""
    try:
        resp = requests.post(EMBEDDING_API_URL, json={"text": text}, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception as e:
        print(f"Embedding API error: {e}")
    return None

def search_similar_chunks(embedding: list, top_k: int = 3, library: str = None):
    """Search for similar doc chunks using cosine similarity."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Convert embedding list to proper format for pgvector
    # pgvector expects format like '[0.1, 0.2, ...]'
    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
    
    # Build query with optional library filter
    if library:
        query = """
            SELECT content, url, library_name, version, 
                   1 - (embedding <=> %s::vector) as similarity
            FROM doc_chunks
            WHERE library_name = %s
            ORDER BY embedding <=> %s::vector LIMIT %s
        """
        params = [embedding_str, library, embedding_str, top_k]
    else:
        query = """
            SELECT content, url, library_name, version, 
                   1 - (embedding <=> %s::vector) as similarity
            FROM doc_chunks
            ORDER BY embedding <=> %s::vector LIMIT %s
        """
        params = [embedding_str, embedding_str, top_k]
    
    try:
        cur.execute(query, params)
        results = cur.fetchall()
    except Exception as e:
        print(f"DB query error: {e}")
        results = []
    
    cur.close()
    conn.close()
    
    return results

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "backend"}

@app.get("/")
def root():
    return {"message": "DocPilot Backend Running"}

@app.post("/answer", response_model=AnswerResponse)
def answer_question(req: QuestionRequest):
    """
    RAG endpoint: Takes a question and returns relevant doc chunks with citations.
    """
    # Step 1: Get embedding for the question
    embedding = get_embedding(req.question)
    if not embedding:
        return AnswerResponse(
            question=req.question,
            citations=[],
            context="Error: Could not generate embedding for question."
        )
    
    # Step 2: Search for similar chunks
    results = search_similar_chunks(embedding, req.top_k, req.library)
    
    if not results:
        return AnswerResponse(
            question=req.question,
            citations=[],
            context="No relevant documentation found."
        )
    
    # Step 3: Build citations and context
    citations = []
    context_parts = []
    
    for content, url, lib, ver, similarity in results:
        citations.append(Citation(
            url=url or "",
            library=lib or "",
            version=ver or "",
            snippet=content[:200] + "..." if len(content) > 200 else content
        ))
        context_parts.append(f"[{lib} {ver}]: {content}")
    
    combined_context = "\n\n---\n\n".join(context_parts)
    
    return AnswerResponse(
        question=req.question,
        citations=citations,
        context=combined_context
    )

@app.get("/stats")
def get_stats():
    """Return stats about indexed documents."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT library_name) FROM doc_chunks")
        total_chunks, total_libs = cur.fetchone()
        cur.close()
        conn.close()
        return {"total_chunks": total_chunks, "total_libraries": total_libs}
    except Exception as e:
        return {"error": str(e)}
