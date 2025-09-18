import faiss
import json
import numpy as np

INPUT = "../data/embeddings/embeddings.jsonl"
INDEX_FILE = "../data/index/faiss_index.index"
META_FILE = "../data/index/meta.jsonl"

def build_faiss_index():
    embeddings = []
    metadata = []

    #this is actually quite simple, we just store embeddings in one array and the data related to it in another array
    with open(INPUT, "r") as infile:
        for line in infile:
            item = json.loads(line)
            embeddings.append(item["embedding"])
            metadata.append({
                "doc_id": item["doc_id"],
                "chunk_index": item["chunk_index"],
                "text": item["text"]
            })

    #then convert the embeddings to a numpy array and create a faiss index
    # Normalize for cosine simin
    embeddings = np.array(embeddings).astype("float32")
    embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)  # cosine normalization
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    #save the index and metadata to files
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "w") as f:
        for item in metadata:
            f.write(json.dumps(item) + "\n")

    print(f"Saved index to {INDEX_FILE}")
    print(f"Saved metadata to {META_FILE}")

if __name__ == "__main__":
    build_faiss_index()