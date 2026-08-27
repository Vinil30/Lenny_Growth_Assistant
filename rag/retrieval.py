from concurrent.futures import ThreadPoolExecutor
import time
from .bm25 import BM25Index, tokenize
from .context import expand_context
from .embeddings import EmbeddingModel
from .hyde import maybe_hyde
from .query_transform import rewrite_query
from .reranking import rerank
from .router import route_query
from .vector_store import FaissVectorStore
from utils.config import settings
from utils.logging import timed


def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, (chunk_id, _score) in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def confidence(rankings):
    ids = [cid for ranking in rankings for cid, _ in ranking[:3]]
    if not ids:
        return {"level": "low", "score": 0.0}
    overlap = len(ids) - len(set(ids))
    score = min(1.0, 0.35 + overlap * 0.18)
    return {"level": "high" if score >= 0.65 else "medium" if score >= 0.45 else "low", "score": round(score, 2)}


class RAGEngine:
    def __init__(self, llm=None):
        self.embedder = EmbeddingModel(settings.embedding_model)
        self.store = FaissVectorStore(settings.rag_data_dir)
        self.ready = False
        self.bm25 = None
        self.llm = llm

    def load(self):
        self.store.load()
        self.bm25 = BM25Index(list(self.store.chunks.values()))
        self.ready = True

    def answer_context(self, query: str, history: list[dict]):
        timings = {}
        with timed(timings, "router"):
            decision = route_query(query, history)
        if not decision["use_rag"]:
            return {"use_rag": False, "contexts": [], "citations": [], "timings": timings, "decision": decision}
        if not self.ready:
            self.load()
        queries = [("original", query)]
        if decision.get("needs_rewrite"):
            with timed(timings, "rewrite"):
                queries.append(("rewrite", rewrite_query(query, history, self.llm)))
        rankings = []
        stage_timings = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for label, q in queries:
                futures.append(executor.submit(self._dense_timed, label, q))
                futures.append(executor.submit(self._sparse_timed, label, q))
            for future in futures:
                ranking, timing = future.result()
                rankings.append(ranking)
                stage_timings.update(timing)
        timings["embedding_ms"] = round(sum(v for k, v in stage_timings.items() if k.endswith("_embedding_ms")), 2)
        timings["faiss_ms"] = round(sum(v for k, v in stage_timings.items() if k.endswith("_faiss_ms")), 2)
        timings["bm25_ms"] = round(sum(v for k, v in stage_timings.items() if k.endswith("_bm25_ms")), 2)
        conf = confidence(rankings)
        if decision.get("use_hyde") or conf["level"] == "low":
            with timed(timings, "hyde"):
                hyde = maybe_hyde(query, history, self.llm)
            if hyde:
                rankings.append(self._dense(hyde))
        with timed(timings, "rrf"):
            fused = rrf(rankings)[:24]
        with timed(timings, "rerank"):
            ranked = rerank(query, fused, self.store.chunks)[:6]
        with timed(timings, "context_expansion"):
            contexts = expand_context(ranked, self.store.chunks, settings.max_context_chars)
        citations = [c["citation"] for c in contexts]
        return {"use_rag": True, "contexts": contexts, "citations": citations, "timings": timings, "decision": decision, "confidence": conf}

    def _dense(self, query):
        vec = self.embedder.encode([query])
        return self.store.search(vec, settings.top_k_dense)

    def _sparse(self, query):
        return self.bm25.search(query, settings.top_k_bm25)

    def _dense_timed(self, label, query):
        start = time.perf_counter()
        vec = self.embedder.encode([query])
        embedding_ms = round((time.perf_counter() - start) * 1000, 2)
        start = time.perf_counter()
        ranking = self.store.search(vec, settings.top_k_dense)
        faiss_ms = round((time.perf_counter() - start) * 1000, 2)
        return ranking, {f"{label}_embedding_ms": embedding_ms, f"{label}_faiss_ms": faiss_ms}

    def _sparse_timed(self, label, query):
        start = time.perf_counter()
        ranking = self.bm25.search(query, settings.top_k_bm25)
        return ranking, {f"{label}_bm25_ms": round((time.perf_counter() - start) * 1000, 2)}
