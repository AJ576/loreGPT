import hashlib
import json

INPUT = "chunked_docs.jsonl"
OUTPUT = "chunked_doc_deduped.jsonl"

seen_hashes = set()
deduped_count = 0
duplicate_count = 0

with open(OUTPUT, "w", encoding="utf-8") as out_f:
    with open(INPUT, "r", encoding="utf-8") as in_f:
        for line in in_f:
            data = json.loads(line)
            text = data["text"].strip()
            h = hashlib.md5(text.encode("utf-8")).hexdigest()

            if h not in seen_hashes:
                seen_hashes.add(h)
                out_f.write(json.dumps(data) + "\n")
                deduped_count += 1
            else:
                duplicate_count += 1
                print(f"Duplicate found: {h} for text: {text[:50]}...")

print(f"\n✅ Deduplication complete.")
print(f"Unique chunks kept: {deduped_count}")
print(f"Duplicates removed: {duplicate_count}")
