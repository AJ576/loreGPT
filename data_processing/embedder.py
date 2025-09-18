import sentence_transformers
import json
from tqdm import tqdm

INPUT = "data/embeddings/chunked_doc_deduped.jsonl"
OUTPUT = "data/embeddings/embeddings.jsonl"
MODEL_NAME = "all-MiniLM-L6-v2"

def embed_all_chunks(INPUT, OUTPUT):
    model = sentence_transformers.SentenceTransformer(MODEL_NAME)
    
    with open(INPUT, "r") as infile, open(OUTPUT, "w") as outfile:
        for line in tqdm(infile, desc="Embedding Chunks"):
            chunk = json.loads(line)
            text = chunk["text"]

            lines = text.strip().split("\n")
            header = lines[0] if lines[0].startswith("## ") else ""
            body = "\n".join(lines[1:]) if header else text

            # Use header+body for embedding to provide semantic cues
            embedding_input = f"{header}\n{body}" if header else text
            embedding = model.encode(embedding_input, normalize_embeddings=True).tolist()

            output = {
                
                "doc_id": chunk["doc_id"],
                "chunk_index": chunk["chunk_index"],
                "header": header,
                "text": body,
                "embedding": embedding
            }

            outfile.write(json.dumps(output) + "\n")

    print(f"Embeddings saved to {OUTPUT}")

if __name__ == "__main__":
    embed_all_chunks(INPUT, OUTPUT)
    print("Embedding process completed.")