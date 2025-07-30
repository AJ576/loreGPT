from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

text = "My name is John Doe. I love programming in Python."
embeddings = model.encode(text)

print(len(embeddings))  # Should print the size of the embedding vector
print(embeddings[:5])  # Print the first 5 elements of the embedding vector

