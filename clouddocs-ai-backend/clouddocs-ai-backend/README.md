# CloudDocs AI — Backend

Event-driven document Q&A platform. Upload a document, it's processed and indexed
in the background (extract → chunk → embed → index), then ask questions and get
answers grounded in the source text, with citations.

## Stack

| Layer | Service | Cost |
|---|---|---|
| API | FastAPI | free (your own code) |
| Hosting | Render (free web service) | free |
| File storage | Supabase Storage (bundled with your Supabase project) | free (1GB) |
| Database | Supabase Postgres | free tier |
| Vector store | ChromaDB (self-hosted, in-process) | free |
| Embeddings | sentence-transformers (local, no API call) | free |
| LLM generation | Groq (Llama 3) | free tier |

## Local setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your real credentials
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs` (FastAPI's auto-generated Swagger UI).

## Getting free credentials

**Supabase (Postgres database + file storage)**
1. Create a project at supabase.com (free tier)
2. Project Settings → Database → copy the connection string into `DATABASE_URL`
3. Storage (sidebar) → New bucket → name it `clouddocs-ai`, keep it private
4. Project Settings → API Keys → reveal the `service_role` secret key → `SUPABASE_SERVICE_KEY`
5. Project Settings → General → copy the Project URL → `SUPABASE_URL`

**Groq (LLM inference)**
1. console.groq.com → API Keys → create a key
2. Fill in `GROQ_API_KEY`

## API endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/documents` | Upload a PDF/TXT file, kicks off background processing |
| GET | `/documents` | List all documents with their status |
| GET | `/documents/{id}` | Get one document's status |
| POST | `/chat/query` | Ask a question about a document (`document_id`, `question`) |

## Deploying to Render (free)

1. Push this backend folder to a GitHub repo
2. Render dashboard → New → Web Service → connect the repo
3. Environment: Docker (uses the included Dockerfile)
4. Add all variables from `.env.example` as environment variables in Render's dashboard
5. Deploy — Render gives you a public URL like `https://clouddocs-ai.onrender.com`

## Known limitation: ChromaDB storage on Render's free tier

Render's free tier has **ephemeral disk** — anything written to disk (including
`CHROMA_PERSIST_DIR`) is wiped on redeploy or when the instance spins down from
inactivity. For a portfolio demo this is usually fine (re-upload a doc to refresh
the index), but if you want persistence across restarts, either:
- Upgrade to a Render paid instance with a persistent disk, or
- Swap ChromaDB for a hosted vector DB with its own free tier (e.g. Pinecone's
  free tier) — `app/vectorstore.py` is the only file you'd need to change.

## Connecting the frontend

The frontend's chat page and upload form should call:
- `POST {API_URL}/documents` (multipart form, field name `file`) for uploads
- `GET {API_URL}/documents/{id}` polled every few seconds to show processing status
- `POST {API_URL}/chat/query` with `{"document_id": "...", "question": "..."}` for Q&A

Set `CORS_ORIGINS` in `.env` to your deployed frontend's URL so the browser allows
the requests.
