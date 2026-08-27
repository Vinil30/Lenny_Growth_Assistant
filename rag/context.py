def expand_context(ranked, chunks_by_id, max_chars):
    ordered = list(chunks_by_id.values())
    pos = {c["chunk_id"]: i for i, c in enumerate(ordered)}
    contexts = []
    used = set()
    budget = max_chars
    for chunk_id, score in ranked:
        if chunk_id not in chunks_by_id or chunk_id in used or budget <= 0:
            continue
        chunk = chunks_by_id[chunk_id]
        neighbors = []
        idx = pos[chunk_id]
        for n in [idx - 1, idx, idx + 1]:
            if 0 <= n < len(ordered) and ordered[n]["episode_id"] == chunk["episode_id"]:
                neighbors.append(ordered[n])
        text_parts = []
        for item in neighbors:
            if item["chunk_id"] in used:
                continue
            used.add(item["chunk_id"])
            text_parts.append(item["text"])
        text = "\n\n".join(text_parts)
        if len(text) > budget:
            text = text[:budget]
        budget -= len(text)
        meta = chunk["metadata"]
        contexts.append(
            {
                "chunk_id": chunk_id,
                "score": score,
                "text": text,
                "citation": {
                    "episode_id": chunk["episode_id"],
                    "episode": meta.get("title", chunk["episode_id"]),
                    "guest": meta.get("guest"),
                    "url": meta.get("youtube_url") or meta.get("url"),
                    "turn_range": [chunk["turn_start"], chunk["turn_end"]],
                },
            }
        )
    return contexts
