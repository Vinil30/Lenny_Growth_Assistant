from .bm25 import tokenize


def rerank(query: str, fused, chunks_by_id):
    q = set(tokenize(query))
    scored = []
    for chunk_id, rrf_score in fused:
        text = chunks_by_id[chunk_id]["embedding_text"]
        overlap = len(q.intersection(tokenize(text))) / max(1, len(q))
        scored.append((chunk_id, rrf_score + overlap * 0.05))
    return sorted(scored, key=lambda x: x[1], reverse=True)
