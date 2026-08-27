# Product Requirements Document

## User And Problem

The primary user is a product or growth operator who wants to mine Lenny's Podcast for trustworthy advice without reading dozens of transcripts. They need grounded synthesis, reusable written content, and rendered artifacts without learning RAG internals or prompt engineering.

## Success Metrics

- A user can ask a product/growth question and receive a cited answer in under a practical local latency budget.
- At least 90% of evaluated answers include a relevant episode citation.
- A fresh evaluator can ingest transcripts, run the app, switch to Ollama, and complete the manual test plan using documented commands.

## Assumptions

- The provided `podcasts/` Markdown files are the authoritative knowledge base.
- The newer implementation brief requiring Flask and Groq overrides the DOCX's FastAPI/cloud examples.
- Local demo quality may vary by Ollama model, so the system exposes fast/main model configuration.
- Full coding-agent logs and demo video are operational deliverables to be added before external submission.

## Scope

Included:

- Flask API, PostgreSQL sessions, web UI, RAG ingestion, FAISS ANN, BM25, RRF, reranking, context expansion, Groq/Ollama providers, Ship 30 essay prompt, artifact generation/viewing, tests, and docs.

Excluded:

- User authentication, streaming UI transport, production deployment hardening, and JavaScript execution inside artifacts. These are useful later but not necessary for the take-home core.

## Core Flows

1. Evaluator deploys on Render or runs locally, configures environment variables, and runs ingestion.
2. User opens the web UI, starts a session, asks a grounded question, and receives citations.
3. User asks a follow-up; recent session context informs query rewriting.
4. User requests a Ship 30 for 30 essay; the assistant uses the dedicated writing instruction plus retrieved evidence.
5. User requests Markdown or HTML/CSS artifact; the artifact is sanitized and rendered in the viewer.

## Acceptance Criteria

- Transcript metadata and ordered speaker turns are parsed.
- Retrieval chunks preserve episode, segment, turn range, speaker, and source metadata.
- FAISS index and chunk metadata persist to disk after ingestion.
- Chat sessions are independent and persisted.
- Groq and Ollama are switchable through environment variables.
- Tests cover critical parser, retrieval, route, and persistence behavior.

## Risks And Trade-offs

- Hallucination: mitigated through explicit evidence-only prompts and citations.
- Latency: mitigated by deterministic routing, precomputed FAISS, bounded top-k, concurrent retrieval, and selective HyDE.
- Local model quality: mitigated by configurable Ollama fast/main models.
- Unsafe artifacts: mitigated by sanitization plus sandboxed iframe rendering.
- Dependency setup: FAISS and sentence-transformers add weight but satisfy the ANN and embedding requirements.

## Implementation Plan

Build the vertical slice first: ingestion, index load, session create, chat answer, citations. Then add latency instrumentation, artifact rendering, essay skill, tests, and documentation. Keep RAG code isolated under `rag/` and route handlers thin.
