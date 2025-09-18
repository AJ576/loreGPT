import json
import re
import tiktoken

INPUT = "../data/embeddings/processed_docs.jsonl"
OUTPUT = "../data/embeddings/chunked_docs.jsonl"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

tokenizer = tiktoken.get_encoding("cl100k_base")

def split_by_headers(text):
    # Match markdown-style headers (## Header Name)
    sections = re.split(r"(## .+)", text)
    if len(sections) <= 1:
        return [text]
    
    # Merge headers with their content
    chunks = []
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        content = sections[i+1].strip() if i+1 < len(sections) else ""
        chunks.append(f"{header}\n{content}")
    return chunks

def split_if_too_long(text, max_tokens=CHUNK_SIZE):
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk = tokens[start:end]
        chunks.append(tokenizer.decode(chunk))
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def process_docs(INPUT, OUTPUT):
    with open(INPUT, "r") as infile, open(OUTPUT, "w") as outfile:
        for line in infile:
            doc = json.loads(line)
            header_chunks = split_by_headers(doc["text"])
            final_chunks = []
            for hchunk in header_chunks:
                subchunks = split_if_too_long(hchunk)
                final_chunks.extend(subchunks)
            for i, chunk in enumerate(final_chunks):
                chunk_doc = {
                    "doc_id": doc["doc_id"],
                    "text": chunk,
                    "chunk_index": i
                }
                outfile.write(json.dumps(chunk_doc) + "\n")
    print(f"Processed {INPUT} with header-based chunking into {OUTPUT}")


if __name__ == "__main__":
    process_docs(INPUT, OUTPUT)
