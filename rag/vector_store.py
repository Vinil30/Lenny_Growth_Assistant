from __future__ import annotations

import json
from pathlib import Path

import numpy as np


class FaissVectorStore:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.index_path = self.data_dir / "index.faiss"
        self.meta_path = self.data_dir / "metadata.json"
        self.chunks_path = self.data_dir / "chunks.json"
        self.index = None
        self.vector_id_to_chunk_id = {}
        self.chunks = {}

    def build(self, vectors: np.ndarray, chunks: list[dict], model_name: str):
        import faiss

        self.data_dir.mkdir(parents=True, exist_ok=True)
        dim = vectors.shape[1]
        index = faiss.IndexHNSWFlat(dim, 32)
        index.hnsw.efConstruction = 80
        index.hnsw.efSearch = 64
        index.add(vectors.astype("float32"))
        faiss.write_index(index, str(self.index_path))
        metadata = {
            "index_type": "IndexHNSWFlat",
            "embedding_model": model_name,
            "dimension": dim,
            "count": len(chunks),
            "vector_id_to_chunk_id": {str(i): c["chunk_id"] for i, c in enumerate(chunks)},
        }
        self.meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        self.chunks_path.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
        self.index = index
        self.vector_id_to_chunk_id = metadata["vector_id_to_chunk_id"]
        self.chunks = {c["chunk_id"]: c for c in chunks}

    def load(self):
        if not self.index_path.exists() or not self.meta_path.exists() or not self.chunks_path.exists():
            raise FileNotFoundError("RAG index not found. Run: python -m rag.ingestion")
        import faiss

        self.index = faiss.read_index(str(self.index_path))
        metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
        chunks = json.loads(self.chunks_path.read_text(encoding="utf-8"))
        self.vector_id_to_chunk_id = metadata["vector_id_to_chunk_id"]
        self.chunks = {c["chunk_id"]: c for c in chunks}

    def search(self, query_vector: np.ndarray, top_k=8):
        if self.index is None:
            self.load()
        distances, ids = self.index.search(query_vector.astype("float32"), top_k)
        results = []
        for dist, vector_id in zip(distances[0], ids[0]):
            if vector_id < 0:
                continue
            chunk_id = self.vector_id_to_chunk_id[str(int(vector_id))]
            results.append((chunk_id, float(dist)))
        return results
