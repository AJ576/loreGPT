import sentence_transformers
import json
from tqdm import tqdm

INPUT = "chunked_docs.jsonl"
OUTPUT = "embeddings.jsonl"
MODEL_NAME = "all-MiniLM-L6-v2"

def embed_all_chunks(INPUT, OUTPUT):
    model = sentence_transformers.SentenceTransformer(MODEL_NAME)
    
    with open(INPUT, "r") as infile, open(OUTPUT, "w") as outfile:
        for line in tqdm(infile, desc="Embedding Chunks"):
            chunk = json.loads(line)
            text = chunk["text"]
            embedding = model.encode(text).tolist()  

            output = {
                "doc_id": chunk["doc_id"],
                "chunk_index": chunk["chunk_index"],
                "text": text,
                "embedding": embedding
            }

            outfile.write(json.dumps(output) + "\n")

    print(f"Embeddings saved to {OUTPUT}")

if __name__ == "__main__":
    embed_all_chunks(INPUT, OUTPUT)
    print("Embedding process completed.")