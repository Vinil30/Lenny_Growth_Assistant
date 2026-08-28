# Architecture

## System

Browser UI -> Flask routes -> services -> RAG engine / LLM provider / database.

Routes only validate requests and serialize responses. `services.chat.ChatService` owns orchestration. The RAG subsystem is self-contained in `rag/`.

## Database Schema

- `chat_sessions`: id, title, provider, user metadata, timestamps.
- `chat_messages`: session id, role, content, citations, timings, timestamp.
- `artifacts`: session id, title, kind, sanitized/renderable content, timestamp.

SQLAlchemy is used for parameterized database access. SQLite is the default deployment database to keep Render setup to one web service; PostgreSQL can still be used by setting `DATABASE_URL`.

## API Endpoints

- `GET /api/health`: database/provider health.
- `POST /api/sessions`: create session.
- `GET /api/sessions`: list recent sessions.
- `GET /api/sessions/<id>`: read session history.
- `POST /api/chat/message`: send a message and receive answer, citations, timings, optional artifact.
- `GET /api/artifacts/<id>`: retrieve an artifact.

## Ingestion Pipeline

1. Parse Markdown front matter metadata.
2. Parse ordered speaker turns using transcript speaker/time headers.
3. Build rolling semantic windows over turns.
4. Embed windows and detect low-similarity topic shifts.
5. Enforce segment size bounds.
6. Split large segments into overlapping retrieval chunks.
7. Embed chunk representation containing episode summary plus local dialogue.
8. Persist FAISS index, vector ID mapping, and chunk metadata.

## FAISS ANN Decision

The dataset is small today, but the requirement asks for genuine ANN and future scalability. `IndexHNSWFlat` is used because it has simple build semantics, strong recall for moderate corpora, no training step, and predictable incremental behavior compared with IVF. Chunk metadata stays outside FAISS in JSON, with `vector_id -> chunk_id` mapping.

## Retrieval

The default path is:

User query -> deterministic router -> original query retrieval -> FAISS ANN + BM25 in parallel -> RRF -> lightweight lexical reranker -> context expansion -> final LLM.

If the query is a follow-up, the fast model rewrites it into a standalone retrieval query while preserving the original query. Original and rewritten representations retrieve independently, then RRF merges them.

HyDE is used only for complex queries or low-confidence retrieval. HyDE output is never treated as evidence; it is only a vector-search representation.

## Retrieval Confidence

Confidence uses bounded, transparent signals: whether top results exist and whether dense/BM25/original/rewrite rankings agree in their top candidates. Low confidence can trigger HyDE. This is intentionally simple and testable.

## Reranking

The reranker combines RRF score with small lexical query overlap. It is fast, local, and avoids sending dozens of chunks to the final LLM. It can be replaced later with a cross-encoder behind the same interface.

## Context Expansion

Each chunk retains episode, segment, turn range, and ordering. For selected chunks, neighboring chunks from the same episode are added, overlaps are deduplicated, and the result is trimmed to `MAX_CONTEXT_CHARS`. This keeps podcast conversation context coherent.

## LLM Providers

`LLMProvider` exposes `generate(prompt, fast, temperature, max_tokens)`. `GroqProvider` calls Groq's OpenAI-compatible chat completions endpoint. `OllamaProvider` calls local `/api/generate`. Fast and main models are configured independently.

## Artifact Security

HTML artifacts are sanitized and rendered in `<iframe sandbox="">`; scripts, iframes, embeds, event attributes, metadata, and `srcdoc` are stripped. Markdown is escaped before lightweight rendering. Generated content never executes in the parent app context.

## Deployment Topology

Render deployment uses one Python web service, Gunicorn, SQLite, and environment variables. PostgreSQL remains optional by setting `DATABASE_URL`.

## Observability

Chat responses include timing fields for routing, rewriting, HyDE, query embedding, FAISS, BM25, RRF, reranking, context expansion, and LLM generation. Structured logging avoids API keys and raw prompts.
