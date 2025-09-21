from sentence_transformers import SentenceTransformer

# Download embedding model to local folder
model_name = "all-MiniLM-L6-v2"
save_path = "backend\data\models\embeddings"

model = SentenceTransformer(model_name)
model.save(save_path)

print("Embedding model saved locally at", save_path)
