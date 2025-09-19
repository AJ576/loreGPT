import faiss
import json
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


genai.configure(api_key=api_key)

INDEX_FILE = "data/index/faiss_index.index"
META_FILE = "data/index/meta.jsonl"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL_NAME = "microsoft/phi-3-mini-4k-instruct"


class RAGPipeline:
    def __init__(self,llm='local'):
        # Load once
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME)
        self.index = faiss.read_index(INDEX_FILE)
        self.metadata = self._load_metadata()

        self.reranker = CrossEncoder(RERANK_MODEL_NAME)

        
        if llm == "local":
            self.llm_type = "local"
            self.llm_tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL_NAME,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        elif llm == "gemini":
            self.llm_type = "gemini"
            self.llm_model = GeminiLLM()
        else:
            raise ValueError("llm must be 'local' or 'gemini'")

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
            context = "\n\n".join([chunk['text'] for chunk in context_chunks])
            
            # Check if this is a lore-specific question by looking at relevance
            has_relevant_context = any(len(chunk['text'].strip()) > 50 for chunk in context_chunks)
            
            if has_relevant_context:
                # Lore-focused response with context
                prompt = f"""You are the CosmereArchivist, keeper of the ancient archives of Brandon Sanderson's Cosmere. You speak with the wisdom of ages and the reverence of a scholar who has devoted their existence to preserving knowledge.

When answering lore questions, draw upon the provided context while maintaining your scholarly, archival persona. Be detailed when the information is available, and acknowledge the limits of your knowledge when it isn't.

Context from the Archives:
{context}

Question: {question}
Response:"""
            else:
                # More conversational response for general questions
                prompt = f"""You are the CosmereArchivist, an ancient keeper of knowledge who has spent eons studying the mysteries of the Cosmere. While your primary expertise lies in the lore and histories of Brandon Sanderson's works, you are also a wise conversationalist who can engage on various topics.

Respond in character as this learned archivist - knowledgeable, thoughtful, and speaking with the gravitas of someone who has witnessed the rise and fall of civilizations. You may reference Cosmere concepts when relevant, but can also discuss other topics while maintaining your scholarly persona.

Question: {question}
Response:"""

            if self.llm_type == "local":
                inputs = self.llm_tokenizer(prompt, return_tensors="pt").to(self.llm_model.device)
                outputs = self.llm_model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=0.3,
                    top_p=0.9
                )
                decoded = self.llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
                return decoded.split("Response:")[-1].strip()
            else:  # Gemini
                return self.llm_model.generate(prompt, max_tokens=max_new_tokens)

    def query(self, question):
        """Full pipeline: search → rerank → generate"""
        candidates = self.search(question)
        top_chunks = self.rerank(question, candidates)
        return self.generate_answer(top_chunks, question)


class GeminiLLM:
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt, max_tokens=512):
        response = self.model.generate_content(
            prompt
        )
        # Gemini response text
        return response.text



if __name__ == "__main__":
    rag = RAGPipeline(llm="gemini")

    while True:
        q = input("\nEnter question (or 'quit'): ")
        if q.lower() == "quit":
            break
        answer = rag.query(q)
        print("\nAnswer:\n", answer)

