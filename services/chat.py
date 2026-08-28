from models import db
from models.database import Artifact, ChatMessage, ChatSession
from rag.retrieval import RAGEngine
from services.artifact import detect_artifact_request, markdown_to_html, sanitize_html
from services.llm import LLMError, get_llm_provider
from utils.config import settings
from utils.logging import timed


SYSTEM = """You are The Lenny Growth Assistant. Answer using only the supplied podcast evidence.
If evidence is insufficient, say so. Distinguish your own synthesis from transcript-grounded claims.
Write clean Markdown: short title, compact sections, bullets or numbered steps, and no Markdown tables.
Use bold only for key labels, not whole sentences. Do not show raw citation dumps at the end.
Mention sources naturally in the text when useful, such as "Elizabeth Stone's Netflix episode".
Do not invent claims."""

SHIP30 = """Create a Ship 30 for 30-style essay of about 1,250 words: strong hook,
clear narrative progression, skimmable headings, a few bullets, selective bold emphasis,
and one specific takeaway. Ground claims in the supplied transcript evidence."""


class ChatService:
    def __init__(self):
        self.llm = _provider()
        self.rag = _rag(self.llm)

    def create_session(self, user_metadata=None):
        session = ChatSession(provider=self.llm.name, user_metadata=user_metadata or {})
        db.session.add(session)
        db.session.commit()
        return session

    def get_history(self, session_id):
        session = ChatSession.query.get(session_id)
        if not session:
            return None
        return [
            {"role": m.role, "content": m.content, "citations": m.citations, "timings": m.timings, "created_at": m.created_at.isoformat()}
            for m in sorted(session.messages, key=lambda m: m.created_at)
        ]

    def respond(self, session_id, message):
        timings = {}
        session = ChatSession.query.get(session_id)
        if not session:
            raise ValueError("Session not found.")
        history = self.get_history(session_id)
        db.session.add(ChatMessage(session_id=session_id, role="user", content=message))
        if session.title == "New conversation":
            session.title = message[:80]
        rag = self.rag.answer_context(message, history)
        timings.update(rag["timings"])
        context_text = "\n\n".join(f"[Source {i+1}] {c['citation']}\n{c['text']}" for i, c in enumerate(rag["contexts"]))
        style = SHIP30 if "ship 30" in message.lower() or "essay" in message.lower() else ""
        artifact_kind = detect_artifact_request(message)
        if artifact_kind is None and len(message.split()) >= 5 and "no artifact" not in message.lower():
            artifact_kind = "html"
        artifact_instruction = ""
        if artifact_kind == "html":
            artifact_instruction = """
Also produce one complete, self-contained HTML/CSS artifact after the answer inside <artifact kind="html">...</artifact>.
Make the artifact the best way to consume the answer: a polished one-page briefing with clear cards, source badges, key takeaways, a decision framework, and next actions when relevant.
Use only HTML and CSS. Do not include scripts, external assets, iframes, or Markdown fences.
"""
        elif artifact_kind == "markdown":
            artifact_instruction = "Also produce one clean Markdown artifact after the answer inside <artifact kind=\"markdown\">...</artifact>."
        prompt = f"{SYSTEM}\n{style}\nConversation history: {history[-6:]}\nEvidence:\n{context_text or 'No podcast evidence retrieved.'}\nUser: {message}\n{artifact_instruction}"
        try:
            with timed(timings, "llm"):
                answer = self.llm.generate(prompt, fast=False, max_tokens=3600 if artifact_kind or style else 1300)
        except LLMError as exc:
            answer = f"I could not reach the configured LLM provider ({self.llm.name}): {exc}"
        artifact = self._extract_artifact(session_id, answer, artifact_kind)
        assistant = ChatMessage(session_id=session_id, role="assistant", content=answer, citations=rag["citations"], timings=timings)
        db.session.add(assistant)
        db.session.commit()
        return {"answer": answer, "citations": rag["citations"], "timings": timings, "artifact": artifact, "provider": self.llm.name}

    def _extract_artifact(self, session_id, answer, kind):
        if not kind:
            return None
        import re

        match = re.search(r"<artifact kind=\"(html|markdown)\">(.*?)</artifact>", answer, re.S)
        if match:
            kind = match.group(1)
            content = match.group(2).strip()
        else:
            visible = re.sub(r"<artifact[\s\S]*?</artifact>", "", answer).strip()
            content = visible or answer
        render = sanitize_html(content) if kind == "html" else markdown_to_html(content)
        artifact = Artifact(session_id=session_id, title="Generated artifact", kind=kind, content=render)
        db.session.add(artifact)
        db.session.flush()
        return {"id": artifact.id, "kind": kind, "content": render}


_LLM = None
_RAG = None


def _provider():
    global _LLM
    if _LLM is None:
        _LLM = get_llm_provider()
    return _LLM


def _rag(llm):
    global _RAG
    if _RAG is None:
        _RAG = RAGEngine(llm)
    return _RAG
