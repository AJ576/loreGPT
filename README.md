# Cosmere Archivist – RAG System

A full-stack **Retrieval-Augmented Generation (RAG)** system that serves as a lore archivist for a massive fictional universe.  
The project crawls and processes thousands of documents into a searchable knowledge base and answers user queries in an in-universe “archivist” voice.

## ✨ Features
- **Custom Data Pipeline** – Crawled, cleaned, and chunked 6,000+ documents into a structured JSON knowledge base.
- **Semantic Search** – FAISS-powered vector index for fast, high-recall retrieval (≈80% lower latency vs brute-force).
- **Generative Q&A** – Integrates Gemini-2.5 API to craft rich, context-aware answers based on retrieved chunks.
- **Full-Stack Prototype** – Next.js frontend with a FastAPI backend, containerized via Docker for easy deployment.

## ⚡ Tech Stack
- **Backend:** Python • FastAPI • FAISS • Gemini API  
- **Frontend:** Next.js (React)  
- **Infrastructure:** Docker (containerized backend), Vercel (frontend hosting)

## 🚀 Architecture
1. **Crawl & Parse:** Custom scraper collects raw text and stores it as JSON.
2. **Pre-processing:** Documents are chunked, embedded, and indexed with FAISS.
3. **Query Flow:**  
   - User submits a question through the frontend.  
   - Backend retrieves the most relevant chunks using semantic search.  
   - Gemini API generates a coherent answer in a lore-expert style.
4. **Deployment:** Frontend deployed on Vercel; backend containerized with Docker (local deployment due to free-tier limits).

## 🛠️ Local Setup
```bash
# Clone repo
git clone https://github.com/AJ576/cosmere-archivist.git
cd cosmere-archivist

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
