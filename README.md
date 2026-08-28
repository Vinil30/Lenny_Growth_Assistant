# Lenny Growth Assistant

A Flask RAG assistant for Lenny's Podcast transcripts. It ingests the provided Markdown podcast files, builds semantic conversation chunks, indexes them with FAISS ANN plus BM25, and serves a polished chat UI with citations, session history, Ship 30 for 30-style essay generation, and a sandboxed artifact viewer.

## Architecture

- `routes/`: thin Flask API layer for health, sessions, chat, and artifacts.
- `services/`: application services for chat orchestration, LLM providers, and artifact safety.
- `rag/`: all parsing, semantic chunking, embeddings, FAISS, BM25, query rewriting, HyDE, RRF, reranking, and context expansion.
- `models/`: SQLite persistence for sessions, messages, and artifacts by default.
- `templates/` and `static/`: simple responsive UI, no heavy frontend framework.

The original DOCX names FastAPI and example cloud providers, while the implementation brief explicitly requires Flask and Groq's OpenAI-compatible API. This submission follows the newer implementation brief and documents that as an assumption.

## Prerequisites

- Python 3.11 recommended
- Ollama for local demo
- Optional Groq API key for cloud mode

## Setup

```bash
pip install -r requirements.txt
Copy-Item .env.example .env
python -m rag.ingestion
python -c "from app import create_app; from models import db; app=create_app(); app.app_context().push(); db.create_all()"
```

Pull local models for Ollama:

```bash
ollama pull llama3.2:3b
ollama pull llama3.1:8b
ollama serve
```

## Environment

Key variables in `.env`:

- `DATABASE_URL`: defaults to `sqlite:///data/app.db` locally; Render uses `sqlite:////tmp/lenny_growth/app.db`.
- `LLM_PROVIDER`: `ollama`, `groq`, or `mock`.
- `GROQ_API_KEY`, `GROQ_BASE_URL`, `GROQ_FAST_MODEL`, `GROQ_MAIN_MODEL`.
- `OLLAMA_BASE_URL`, `OLLAMA_FAST_MODEL`, `OLLAMA_MAIN_MODEL`.
- `EMBEDDING_MODEL`: label for the embedding configuration. The required default path uses a deterministic local hash embedder to keep setup fast; `rag/embeddings.py` can use `sentence-transformers` automatically if you add it later.
- `TRANSCRIPT_DIR`: defaults to `podcasts`.
- `RAG_DATA_DIR`: defaults to `data/faiss`.

## Ingest Transcripts

```bash
python -m rag.ingestion
```

This parses Markdown front matter and speaker turns, builds semantic conversation segments, creates retrieval chunks, precomputes local embeddings, writes a FAISS `IndexHNSWFlat` ANN index to `data/faiss/index.faiss`, and persists `metadata.json` plus `chunks.json`.

If the index is missing, the chat endpoint returns a clear `503` telling you to run ingestion.

## Run Locally

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

## Render Deploy

This repo includes `render.yaml`. On Render, use one Web Service only:

- Build command: `pip install -r requirements.txt && python -m rag.ingestion`
- Start command: `gunicorn app:app`
- Environment variables: `GROQ_API_KEY`, `GROQ_FAST_MODEL`, `GROQ_MAIN_MODEL`

No separate Render PostgreSQL service is required for the simple demo setup. Sessions are stored in SQLite under `/tmp` on Render; this is easiest for evaluation, but redeploys or restarts can reset session storage.

Render's Flask guide recommends Gunicorn with `gunicorn app:app`.

## Groq Mode

Set:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=...
GROQ_FAST_MODEL=openai/gpt-oss-20b
GROQ_MAIN_MODEL=openai/gpt-oss-120b
```

Groq is called through `/openai/v1/chat/completions`. For local development, copy `.env.example` to `.env` and put the real API key in `.env`; `.env.example` is only a template and should not contain secrets.

## Ollama Mode

Set:

```env
LLM_PROVIDER=ollama
OLLAMA_FAST_MODEL=llama3.2:3b
OLLAMA_MAIN_MODEL=llama3.1:8b
```

The fast model is used for rewrite/HyDE work. The main model is used for final grounded answers, essays, and artifacts. Errors such as unavailable Ollama, missing models, and timeouts are returned gracefully in the chat response.

## Latency Strategy

The common path avoids LLM routing. A deterministic router decides whether RAG is needed and whether rewrite or HyDE is justified. Dense FAISS and BM25 retrieval run concurrently for each query representation. HyDE is only used for complex queries or low retrieval confidence.

Logged/returned timings include:

`router_ms`, `rewrite_ms`, `hyde_ms`, `embedding_ms`, `faiss_ms`, `bm25_ms`, `rrf_ms`, `rerank_ms`, `context_expansion_ms`, `llm_ms`.

## Artifact Security

Generated HTML is treated as untrusted. The app strips scripts, iframes, embeds, event handlers, metadata, and `srcdoc`, then renders the result in an `<iframe sandbox="">`. Markdown artifacts are escaped before minimal formatting. The parent app never injects generated HTML directly into its DOM.

## Tests

```bash
pytest
```

Unit tests do not require live Groq, Ollama, FAISS index files, or PostgreSQL.
`pytest.ini` keeps pytest temp/cache files inside the workspace to avoid host temp-directory permission issues.

Latest local verification:

```text
python -m pytest tests
9 passed
```

## Manual UI Test Plan

1. Start the Flask app.
2. Run ingestion.
3. Open the UI and create a new conversation.
4. Ask: `How should startups think about hiring executives?`
5. Confirm the answer cites one or more podcast episodes.
6. Ask a follow-up: `What about references?`
7. Confirm the follow-up preserves context.
8. Ask for a `Ship 30 for 30 essay about that`.
9. Ask for an `HTML artifact summarizing the framework`.
10. Confirm the artifact appears in the sandboxed viewer.

## Troubleshooting

- Missing FAISS index: run `python -m rag.ingestion`.
- Ollama connection failure: run `ollama serve` and pull the configured models.
- Groq failure: verify `GROQ_API_KEY` and configured model names. A `404` usually means the API key works but the configured model ID is unavailable or misspelled.
- Database failure: verify `DATABASE_URL`. The simple local default is SQLite at `sqlite:///data/app.db`; Render should use `sqlite:////tmp/lenny_growth/app.db`.
