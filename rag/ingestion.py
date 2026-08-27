from .chunking import chunk_to_dict, make_chunks
from .embeddings import EmbeddingModel
from .parsing import parse_episodes
from .vector_store import FaissVectorStore
from utils.config import settings
from utils.logging import configure_logging, log_event


def ingest(transcript_dir=None, data_dir=None):
    transcript_dir = transcript_dir or settings.transcript_dir
    data_dir = data_dir or settings.rag_data_dir
    configure_logging()
    episodes = parse_episodes(transcript_dir)
    embedder = EmbeddingModel(settings.embedding_model)
    chunks = [chunk_to_dict(c) for c in make_chunks(episodes, embedder)]
    vectors = embedder.encode([c["embedding_text"] for c in chunks])
    store = FaissVectorStore(data_dir)
    store.build(vectors, chunks, settings.embedding_model)
    log_event("ingestion_complete", episodes=len(episodes), chunks=len(chunks), data_dir=data_dir)
    return {"episodes": len(episodes), "chunks": len(chunks), "data_dir": data_dir}


if __name__ == "__main__":
    print(ingest())
