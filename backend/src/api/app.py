from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.rag_pipeline import RAGPipeline

# Load pipeline once at startup
rag = RAGPipeline()

# Define request/response schemas
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

class Chunk(BaseModel):
    doc_id: str
    chunk_index: int
    text: str

class SearchResponse(BaseModel):
    chunks: List[Chunk]

# Init FastAPI app
app = FastAPI(title="CopperMind RAG API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://cosmere-archivist.vercel.app"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.post("/ask", response_model=QueryResponse)
def ask_question(req: QueryRequest):
    answer = rag.query(req.question)
    return QueryResponse(answer=answer)

@app.post("/search", response_model=SearchResponse)
def search_chunks(req: QueryRequest, top_k: int = 5):
    """Retrieve top-k chunks (reranked) without generating an answer."""
    candidates = rag.search(req.question, top_k=top_k)
    reranked = rag.rerank(req.question, candidates, top_k=top_k)
    return SearchResponse(chunks=reranked)

