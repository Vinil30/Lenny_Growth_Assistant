from pathlib import Path
import uuid

from rag.bm25 import BM25Index
from rag.chunking import make_chunks
from rag.embeddings import EmbeddingModel
from rag.parsing import parse_episode
from rag.retrieval import confidence, rrf
from rag.router import route_query


def _workspace_tmp():
    path = Path("tests") / "_tmp" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_parse_episode_metadata_and_turns():
    path = _workspace_tmp() / "episode.md"
    path.write_text(
        '---\ntitle: "Product strategy"\nguest: "Guest Name"\nyoutube_url: "https://example.com"\n---\n\n'
        "**Lenny Rachitsky** (00:00:01):\nWhat should teams build?\n\n"
        "**Guest Name** (00:00:03):\nThey should talk to customers first.\n",
        encoding="utf-8",
    )
    episode = parse_episode(path)
    assert episode.metadata["title"] == "Product strategy"
    assert episode.turns[0].speaker == "Lenny Rachitsky"
    assert episode.turns[1].text == "They should talk to customers first."


def test_semantic_chunk_preserves_source_metadata():
    path = _workspace_tmp() / "episode.md"
    body = "\n\n".join(f"**Speaker {i % 2}** (00:00:{i:02d}):\nText about retention and product growth {i}." for i in range(10))
    path.write_text('---\ntitle: "Retention"\nguest: "Guest"\n---\n\n' + body, encoding="utf-8")
    episode = parse_episode(path)
    chunks = make_chunks([episode], EmbeddingModel("local-test"))
    assert chunks
    assert chunks[0].metadata["guest"] == "Guest"
    assert chunks[0].turn_start <= chunks[0].turn_end


def test_bm25_retrieval_finds_exact_terms():
    chunks = [
        {"chunk_id": "a", "embedding_text": "pricing packaging enterprise sales"},
        {"chunk_id": "b", "embedding_text": "consumer retention activation loops"},
    ]
    results = BM25Index(chunks).search("enterprise pricing")
    assert results[0][0] == "a"


def test_rrf_and_confidence():
    rankings = [[("a", 1.0), ("b", 0.5)], [("a", 0.7), ("c", 0.2)]]
    assert rrf(rankings)[0][0] == "a"
    assert confidence(rankings)["level"] in {"medium", "high"}


def test_router_skips_small_talk_and_rewrites_followups():
    assert route_query("hello", [])["use_rag"] is False
    decision = route_query("What about hiring there?", [{"role": "user", "content": "What did Brian say about CEOs?"}])
    assert decision["use_rag"] is True
    assert decision["needs_rewrite"] is True
