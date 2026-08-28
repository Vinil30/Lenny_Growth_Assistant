import re
from html import escape


def detect_artifact_request(text: str) -> str | None:
    q = text.lower()
    if "no artifact" in q or "without artifact" in q:
        return None
    if "html" in q and ("artifact" in q or "generate" in q or "create" in q):
        return "html"
    if "markdown" in q or "artifact" in q:
        return "markdown"
    if any(word in q for word in ("compare", "framework", "plan", "strategy", "prioritize", "summary", "summarize", "organize", "organise")):
        return "html"
    return None


def sanitize_html(html: str) -> str:
    html = re.sub(r"<\s*(script|iframe|object|embed|link|meta)\b[^>]*>.*?<\s*/\s*\1\s*>", "", html, flags=re.I | re.S)
    html = re.sub(r"<\s*(script|iframe|object|embed|link|meta)\b[^>]*\/?\s*>", "", html, flags=re.I)
    html = re.sub(r"\s+on[a-zA-Z]+\s*=\s*(['\"]).*?\1", "", html, flags=re.S)
    html = re.sub(r"\s+srcdoc\s*=\s*(['\"]).*?\1", "", html, flags=re.I | re.S)
    html = re.sub(r"javascript\s*:", "", html, flags=re.I)
    return html


def markdown_to_html(md: str) -> str:
    html = escape(md)
    html = re.sub(r"^### (.*)$", r"<h3>\1</h3>", html, flags=re.M)
    html = re.sub(r"^## (.*)$", r"<h2>\1</h2>", html, flags=re.M)
    html = re.sub(r"^# (.*)$", r"<h1>\1</h1>", html, flags=re.M)
    html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)
    html = html.replace("\n", "<br>")
    return html
