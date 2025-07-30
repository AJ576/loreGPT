import json
import tiktoken

INPUT = "processed_docs.jsonl"
OUTPUT = "chunked_docs.jsonl"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_text(text):
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk = tokens[start:end]
        chunks.append(tokenizer.decode(chunk))
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks

def process_docs(INPUT,OUTPUT):
    with open(INPUT, "r") as infile, open(OUTPUT, "w") as outfile:
        for line in infile:
            doc = json.loads(line)
            chunks = chunk_text(doc["text"])
            for i, chunk in enumerate(chunks):
                chunk_doc = {
                    "doc_id": doc["doc_id"],
                    "text": chunk,
                    "chunk_index": i
                }
                outfile.write(json.dumps(chunk_doc) + "\n")
    print(f"Processed {INPUT} and saved chunked documents to {OUTPUT}")
if __name__ == "__main__":
    process_docs(INPUT, OUTPUT)