import re

SMALL_TALK = {"hi", "hello", "hey", "thanks", "thank you", "who are you"}
DOMAIN_WORDS = {
    "product", "growth", "startup", "founder", "pm", "pricing", "hiring", "team",
    "ai", "strategy", "feature", "retention", "activation", "podcast", "lenny",
    "essay", "artifact", "ship 30", "go-to-market", "marketplace"
}


def route_query(query: str, history: list[dict] | None = None) -> dict:
    q = query.lower().strip()
    if q in SMALL_TALK or len(q.split()) <= 2 and not any(w in q for w in DOMAIN_WORDS):
        return {"use_rag": False, "needs_rewrite": False, "use_hyde": False}
    tokens = re.findall(r"[a-z0-9']+", q)
    needs_rewrite = any(x in tokens for x in ["it", "that", "this", "those", "he", "she", "there", "they"]) and bool(history)
    use_hyde = len(q.split()) > 22 or "compare" in q or "framework" in q
    return {"use_rag": True, "needs_rewrite": needs_rewrite, "use_hyde": use_hyde}
