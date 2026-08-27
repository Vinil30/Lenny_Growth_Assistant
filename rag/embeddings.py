from __future__ import annotations

import hashlib
import math
from typing import Iterable

import numpy as np


class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self.dimension = 384

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                self.dimension = int(self._model.get_sentence_embedding_dimension())
            except Exception:
                self._model = False
        return self._model

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        texts = list(texts)
        model = self._load()
        if model:
            vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(vectors, dtype="float32")
        return np.asarray([self._hash_embed(t) for t in texts], dtype="float32")

    def _hash_embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
