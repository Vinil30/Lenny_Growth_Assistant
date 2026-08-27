def rewrite_query(query: str, history: list[dict], llm=None) -> str:
    recent = " ".join(m["content"][:300] for m in history[-4:] if m.get("role") == "user")
    if llm:
        prompt = f"Rewrite this follow-up as a standalone retrieval query. Keep names and intent.\nContext: {recent}\nQuery: {query}"
        try:
            return llm.generate(prompt, fast=True, temperature=0.1, max_tokens=160).strip() or query
        except Exception:
            pass
    return f"{recent} {query}".strip()
