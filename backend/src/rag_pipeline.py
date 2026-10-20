import faiss
import json
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Reduce PyTorch memory footprint
try:
    import torch
    torch.set_num_threads(1)
except Exception:
    pass

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Configuration flags
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "false").lower() in ("true", "1", "yes")

# File paths and model names
INDEX_FILE = "data/index/faiss_index.index"
META_FILE = "data/index/meta.jsonl"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

class LineIndexedJSONL:
    """Memory-efficient JSONL reader using file byte offsets (< 1 MB RAM vs 80 MB for raw dicts)."""
    def __init__(self, filepath):
        self.filepath = filepath
        self.offsets = []
        with open(filepath, "rb") as f:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                self.offsets.append(offset)
        self.file = open(filepath, "r", encoding="utf-8")

    def __getitem__(self, idx):
        self.file.seek(self.offsets[idx])
        line = self.file.readline()
        return json.loads(line)

class GeminiLLM:
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt, max_tokens=512):
        response = self.model.generate_content(prompt)
        return response.text

class RAGPipeline:
    def __init__(self):
        # Load models / index
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME)
        self.index = faiss.read_index(INDEX_FILE, faiss.IO_FLAG_MMAP)  # memory-map
        self.metadata = LineIndexedJSONL(META_FILE)

        # CrossEncoder is ~150MB of RAM; keep disabled by default on 512MB free tier
        self.reranker = None
        if ENABLE_RERANKER:
            from sentence_transformers import CrossEncoder
            self.reranker = CrossEncoder(RERANK_MODEL_NAME)

        # Only Gemini LLM
        self.llm_type = "gemini"
        self.llm_model = GeminiLLM()

    def search(self, query, top_k=20):
        """Retrieve top_k candidate chunks using vector similarity"""
        query_vector = self.embedder.encode(query).astype("float32").reshape(1, -1)
        query_vector /= (query_vector ** 2).sum(axis=1, keepdims=True) ** 0.5  # normalize

        D, I = self.index.search(query_vector, top_k)
        results = []
        for idx in I[0]:
            item = self.metadata[idx]
            results.append({
                "doc_id": item["doc_id"],
                "chunk_index": item["chunk_index"],
                "text": item["text"]
            })
        return results

    def rerank(self, query, candidates, top_k=3):
        """Rerank candidate chunks using cross-encoder if enabled, else return top FAISS matches"""
        if self.reranker:
            pairs = [(query, c['text']) for c in candidates]
            scores = self.reranker.predict(pairs)
            ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
            return [c for c, _ in ranked[:top_k]]
        return candidates[:top_k]

    def generate_answer(self, context_chunks, question, max_new_tokens=512):
        context = "\n\n".join([chunk['text'] for chunk in context_chunks])
        has_relevant_context = any(len(chunk['text'].strip()) > 50 for chunk in context_chunks)

        if has_relevant_context:
            prompt = f"""You are the CosmereArchivist, keeper of the ancient archives of Brandon Sanderson's Cosmere. Draw upon the provided context while maintaining your scholarly persona.

Context from the Archives:
{context}

Question: {question}
Response:"""
        else:
            prompt = f"""You are the CosmereArchivist, an ancient keeper of knowledge. Respond in character as a learned archivist.

Question: {question}
Response:"""

        return self.llm_model.generate(prompt, max_tokens=max_new_tokens)

    def query(self, question):
        """Full pipeline: search → rerank → generate"""
        candidates = self.search(question, top_k=5 if not self.reranker else 20)
        top_chunks = self.rerank(question, candidates, top_k=3)
        return self.generate_answer(top_chunks, question)

if __name__ == "__main__":
    rag = RAGPipeline()
    while True:
        q = input("\nEnter question (or 'quit'): ")
        if q.lower() == "quit":
            break
        answer = rag.query(q)
        print("\nAnswer:\n", answer)