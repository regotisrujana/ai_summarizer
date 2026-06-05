# AI Summarizer and Domain-Specific RAG Chatbot

Full stack AI project with two modes:

- Summarize pasted text, article URLs, or YouTube transcripts with Groq.
- Chat with a domain-specific RAG knowledge base about AI summarization and retrieval systems.

The RAG project includes 50 source documents, source citations, retrieval accuracy evaluation, and answer quality scoring.

## Project structure

```text
ai_summarizer/
  backend/
    app.py                    # FastAPI routes
    rag.py                    # BM25 retrieval, answer generation, evaluation
    data/
      rag_documents.json      # 50 source documents
      rag_eval.json           # evaluation questions and reference answers
    scraper.py                # URL and YouTube scraping
    database.py               # MongoDB save
    requirements.txt
    .env.example
  frontend/
    src/
      App.jsx                 # Summarizer, RAG chat, evaluation UI
      api.js                  # Axios API helper
      main.jsx
    package.json
    .env.example
  README.md
```

## Features

- FastAPI backend
- React and Vite frontend
- Groq-powered summarization
- Domain-specific RAG chatbot
- 50-document local knowledge base
- BM25 keyword retrieval
- Source citations with document ids, titles, categories, and scores
- Evaluation metrics:
  - Top-1 retrieval accuracy
  - Top-3 retrieval accuracy
  - Mean reciprocal rank
  - Answer quality F1 against reference answers

## Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/ai_summarizer?retryWrites=true&w=majority
```

Run the backend:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

API docs:

```text
http://localhost:8000/docs
```

## Frontend setup

```bash
cd frontend
npm install
copy .env.example .env
```

Edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Run:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

## API endpoints

### Health

```text
GET /
```

### Summarization

```text
POST /summarize
```

```json
{
  "text": "optional pasted content",
  "url": "https://example.com/article"
}
```

### RAG chatbot

```text
POST /chat
```

```json
{
  "question": "How can retrieval accuracy be evaluated?",
  "top_k": 3
}
```

Response includes:

```json
{
  "answer": "Generated answer with citations.",
  "sources": [
    {
      "id": "D013",
      "title": "Retrieval Accuracy",
      "category": "evaluation",
      "text": "Source text...",
      "score": 4.21
    }
  ]
}
```

### RAG evaluation

```text
GET /rag/evaluate
```

Returns document count, question count, top-1 accuracy, top-3 accuracy, MRR, answer F1, and per-question results.

## Deploy backend on Render

Create a Render Web Service:

```text
Root Directory: backend
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
PYTHON_VERSION=3.11.9
GROQ_API_KEY=your Groq key
MONGO_URI=your MongoDB URI
```

Use Python 3.11.9 to avoid package build issues with newer Python versions.

## Deploy frontend on Render

Create a Render Static Site:

```text
Root Directory: frontend
Build Command: npm install && npm run build
Publish Directory: dist
```

Environment variable:

```text
VITE_API_URL=https://your-backend-service.onrender.com
```

After changing `VITE_API_URL`, redeploy the frontend because Vite reads this value at build time.

## Project requirement mapping

Requirement: Build a domain-specific RAG chatbot with at least 50 source documents; evaluate retrieval accuracy and answer quality.

Implemented:

- Domain: AI summarization and RAG systems
- Source documents: `backend/data/rag_documents.json` contains 50 documents
- Chatbot: `POST /chat` and the RAG Chat tab in the frontend
- Retrieval accuracy: top-1, top-3, and MRR in `GET /rag/evaluate`
- Answer quality: token F1 against reference answers in `GET /rag/evaluate`
- UI: Evaluation tab displays metrics and per-question results

## Troubleshooting

| Issue | Fix |
| --- | --- |
| Render metadata-generation-failed | Set `PYTHON_VERSION=3.11.9`, then clear build cache and redeploy |
| Frontend cannot reach backend | Set `VITE_API_URL` to the backend Render URL |
| MongoDB save warning | Check `MONGO_URI` and Atlas network access |
| Groq key error | Add `GROQ_API_KEY` to backend environment variables |
| First Render request is slow | Free services may sleep; wait and retry |

## License

MIT
