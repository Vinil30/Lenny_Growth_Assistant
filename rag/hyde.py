def maybe_hyde(query: str, history: list[dict], llm=None) -> str | None:
    if not llm:
        return None
    prompt = (
        "Write a short hypothetical podcast transcript passage that would answer this query. "
        "This is only for retrieval representation, not evidence.\nQuery: "
        + query
    )
    try:
        return llm.generate(prompt, fast=True, temperature=0.2, max_tokens=220).strip()
    except Exception:
        return None
