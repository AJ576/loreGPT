# src/ingest.py

import os
import json

INPUT_FOLDER = "data/"
OUTPUT_FILE = "processed_docs.jsonl"  # line-delimited JSON output

def normalize_article(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "Untitled")
    sections = data.get("sections", {})

    parts = [f"# {title}"]
    for sec, content in sections.items():
        content = content.strip()
        if content:
            parts.append(f"\n## {sec}\n{content}")
    
    full_text = "\n".join(parts)
    return {"doc_id": title, "text": full_text}


def batch_ingest(input_folder, output_path):
    with open(output_path, "w", encoding="utf-8") as out_f:
        for fname in os.listdir(input_folder):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(input_folder, fname)
            try:
                doc = normalize_article(path)
                out_f.write(json.dumps(doc) + "\n")
            except Exception as e:
                print(f"[!] Failed to process {fname}: {e}")

if __name__ == "__main__":
    batch_ingest(INPUT_FOLDER, OUTPUT_FILE)
    print("Done. Articles written to:", OUTPUT_FILE)
