from sentence_transformers import CrossEncoder

model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
save_path = "backend\data\models\\reranker"

model = CrossEncoder(model_name)
model.save(save_path)

print("Reranker model saved locally at", save_path)
