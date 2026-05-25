# AI Content Summarizer

Beginner-friendly full stack app: paste text or a URL, get an AI summary (Groq), stored in MongoDB.

## Folder structure

```
ai_summarizer/
├── backend/
│   ├── app.py           # FastAPI + POST /summarize
│   ├── scraper.py       # URL scraping (newspaper3k)
│   ├── database.py      # MongoDB save
│   ├── requirements.txt
│   └── .env             # GROQ_API_KEY, MONGO_URI (create from .env.example)
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Single-page UI
│   │   ├── main.jsx
│   │   └── api.js       # Axios calls
│   ├── package.json
│   └── .env             # VITE_API_URL (create from .env.example)
└── README.md
```

---

## 1. MongoDB Atlas setup (~5 min)

1. Go to [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and create a free account.
2. Create a **free M0 cluster**.
3. **Database Access** → Add user (username + password). Save the password.
4. **Network Access** → Add IP → **Allow Access from Anywhere** (`0.0.0.0/0`) for dev/deploy simplicity.
5. **Database** → Connect → **Drivers** → copy the connection string.
6. Replace `<password>` with your user password and add a database name before `?`:

   ```
   mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/ai_summarizer?retryWrites=true&w=majority
   ```

7. Collection `summaries` is created automatically on first save.

---

## 2. Groq API key

1. Sign up at [https://console.groq.com](https://console.groq.com).
2. Create an API key.
3. Model used: `llama-3.1-8b-instant` (replaces decommissioned `llama3-8b-8192`).

---

## 3. Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows — or: cp .env.example .env
```

Edit `backend/.env`:

```env
GROQ_API_KEY=gsk_...
MONGO_URI=mongodb+srv://...
```

Run:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

API: [http://localhost:8000](http://localhost:8000)  
Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 4. Frontend setup

```bash
cd frontend
npm install
copy .env.example .env   # Windows
```

Edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Run:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## API: POST /summarize

**Request**

```json
{
  "text": "optional pasted content",
  "url": "https://example.com/article"
}
```

- If `url` is set → scrape and summarize (URL wins over text).
- Else → summarize `text`.
- Returns **all important points** as a bullet list (no short/medium/long).

**Response**

```json
{
  "summary": "- point one\n- point two\n..."
}
```

---

## Deploy backend (Render)

1. Push this repo to GitHub.
2. [https://dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**.
3. Connect the repo.
4. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables:**
   - `GROQ_API_KEY` = your key
   - `MONGO_URI` = Atlas connection string
6. Deploy. Copy the service URL (e.g. `https://ai-summarizer-xxxx.onrender.com`).

Free tier may sleep; first request can take ~30s.

---

## Deploy frontend (Vercel)

1. [https://vercel.com](https://vercel.com) → **Add New Project** → import GitHub repo.
2. Settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. **Environment Variable:**
   - `VITE_API_URL` = your Render URL (no trailing slash), e.g. `https://ai-summarizer-xxxx.onrender.com`
4. Deploy.

Test: open Vercel URL → paste text or URL → **Summarize**.

---

## Quick test (curl)

```bash
curl -X POST http://localhost:8000/summarize ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Python is a popular programming language used for web apps, data science, and automation.\",\"url\":\"\"}"
```

(macOS/Linux: use `\` instead of `^` for line breaks, or single line.)

---

## Troubleshooting

| Issue | Fix |
|--------|-----|
| CORS / network error | Set `VITE_API_URL` to exact Render HTTPS URL |
| MongoDB error | Include DB name in URI: `.../ai_summarizer?...` |
| URL scrape fails | Some sites block bots; paste text instead |
| YouTube fails | Enable CC/subtitles on the video; upgrade backend (`pip install youtube-transcript-api==1.2.4`) |
| Groq model error | Check [Groq models](https://console.groq.com/docs/models); update `model` in `app.py` if retired |
| Render cold start | Wait and retry first request |

---

## License

MIT — use freely for learning and portfolios.
