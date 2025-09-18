import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_FILE = "faiss_index.index"
META_FILE = "meta.jsonl"
MODEL_NAME = "all-MiniLM-L6-v2"

def load_metadata():
    metadata = []
    with open(META_FILE, "r") as f:
        for line in f:
            metadata.append(json.loads(line))
    return metadata

def search(query, top_k=5):
    model = SentenceTransformer(MODEL_NAME)
    query_vector = model.encode(query).astype("float32").reshape(1, -1)
    query_vector /= np.linalg.norm(query_vector, axis=1, keepdims=True)  # Normalize for cosine sim

    index = faiss.read_index(INDEX_FILE)
    metadata = load_metadata()

    D, I = index.search(query_vector, top_k)
    results = []

    for idx in I[0]:
        item = metadata[idx]
        results.append({
            "doc_id": item["doc_id"],
            "chunk_index": item["chunk_index"],
            "text": item["text"]
        })

    return results

if __name__ == "__main__":
    query = input("Enter your question: ")
    results = search(query)

    print("\nTop matching chunks:\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['text']}\n")
    print("\nSearch completed.")