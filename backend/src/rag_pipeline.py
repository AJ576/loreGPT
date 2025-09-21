import faiss
import json
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import numpy as np
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

INDEX_FILE = "data/index/faiss_index.index"
META_FILE = "data/index/meta.jsonl"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # keep same model so index still works

class GeminiLLM:
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt, max_tokens=512):
        response = self.model.generate_content(prompt)
        return response.text

class RAGPipeline:
    def __init__(self):
        # Lazy-load embedder to save cold-start RAM
        self._embedder = None
        # memory-map index to avoid copying to RAM
        self.index = faiss.read_index(INDEX_FILE, faiss.IO_FLAG_MMAP)
        self.metadata = self._load_metadata()
        self.llm = GeminiLLM()

    @property
    def embedder(self):
        # load on first use
        if self._embedder is None:
            self._embedder = SentenceTransformer(EMBED_MODEL_NAME)
        return self._embedder

    def _load_metadata(self):
        with open(META_FILE, "r") as f:
            return [json.loads(line) for line in f]

    def search(self, query, top_k=10):
        qv = self.embedder.encode(query).astype("float32").reshape(1, -1)
        # normalize for cosine similarity
        qv /= np.linalg.norm(qv, axis=1, keepdims=True)
        D, I = self.index.search(qv, top_k)
        return [self.metadata[idx] for idx in I[0]]

    def generate_answer(self, context_chunks, question, max_new_tokens=512):
        context = "\n\n".join(c['text'] for c in context_chunks)
        prompt = (
            f"You are the CosmereArchivist.\n\nContext:\n{context}\n\n"
            f"Question: {question}\nResponse:"
        )
        return self.llm.generate(prompt, max_tokens=max_new_tokens)

    def query(self, question):
        top_chunks = self.search(question, top_k=5)
        return self.generate_answer(top_chunks, question)

if __name__ == "__main__":
    rag = RAGPipeline()
    while True:
        q = input("\nEnter question (or 'quit'): ")
        if q.lower() == "quit":
            break
        print("\nAnswer:\n", rag.query(q))
