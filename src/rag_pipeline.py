import faiss
import json
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import AutoTokenizer, AutoModelForCausalLM


INDEX_FILE = "data/index/faiss_index.index"
META_FILE = "data/index/meta.jsonl"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL_NAME = "microsoft/phi-3-mini-4k-instruct"


class RAGPipeline:
    def __init__(self):
        # Load once
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME)
        self.index = faiss.read_index(INDEX_FILE)
        self.metadata = self._load_metadata()

        self.reranker = CrossEncoder(RERANK_MODEL_NAME)

        self.llm_tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    def _load_metadata(self):
        metadata = []
        with open(META_FILE, "r") as f:
            for line in f:
                metadata.append(json.loads(line))
        return metadata

    def search(self, query, top_k=20):
        """Retrieve top_k candidate chunks using vector similarity"""
        query_vector = self.embedder.encode(query).astype("float32").reshape(1, -1)
        query_vector /= np.linalg.norm(query_vector, axis=1, keepdims=True)  # normalize

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
        """Generate final answer from top context chunks"""
        context = "\n\n".join([chunk['text'] for chunk in context_chunks])
        prompt = f"""You are a lore assistant. Answer the following question using only the given context from the lore. Be factual.

Context:
{context}

Question: {question}
Answer:"""

        inputs = self.llm_tokenizer(prompt, return_tensors="pt").to(self.llm_model.device)
        outputs = self.llm_model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.3,
            top_p=0.9
        )

        decoded = self.llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = decoded.split("Answer:")[-1].strip()
        return answer

    def query(self, question):
        """Full pipeline: search → rerank → generate"""
        candidates = self.search(question)
        top_chunks = self.rerank(question, candidates)
        return self.generate_answer(top_chunks, question)


# For direct testing
if __name__ == "__main__":
    rag = RAGPipeline()
    while True:
        q = input("\nEnter question (or 'quit'): ")
        if q.lower() == "quit":
            break
        answer = rag.query(q)
        print("\nAnswer:\n", answer)
