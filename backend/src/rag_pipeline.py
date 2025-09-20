import faiss
import json
from sentence_transformers import SentenceTransformer, CrossEncoder
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# File paths and model names
INDEX_FILE = "data/index/faiss_index.index"
META_FILE = "data/index/meta.jsonl"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

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
        self.metadata = self._load_metadata()
        self.reranker = CrossEncoder(RERANK_MODEL_NAME)

        # Only Gemini LLM
        self.llm_type = "gemini"
        self.llm_model = GeminiLLM()

    def _load_metadata(self):
        metadata = []
        with open(META_FILE, "r") as f:
            for line in f:
                metadata.append(json.loads(line))
        return metadata

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
        """Rerank candidate chunks using cross-encoder"""
        pairs = [(query, c['text']) for c in candidates]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]

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
        candidates = self.search(question)
        top_chunks = self.rerank(question, candidates)
        return self.generate_answer(top_chunks, question)

if __name__ == "__main__":
    rag = RAGPipeline()
    while True:
        q = input("\nEnter question (or 'quit'): ")
        if q.lower() == "quit":
            break
        answer = rag.query(q)
        print("\nAnswer:\n", answer)