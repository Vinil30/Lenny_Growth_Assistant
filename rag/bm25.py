import math
import re
from collections import Counter, defaultdict


TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self, chunks=None, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.chunks = chunks or []
        self.doc_freq = defaultdict(int)
        self.doc_tokens = []
        self.avgdl = 1
        if chunks:
            self.build(chunks)

    def build(self, chunks):
        self.chunks = chunks
        lengths = []
        for chunk in chunks:
            tokens = tokenize(chunk["embedding_text"])
            self.doc_tokens.append(Counter(tokens))
            lengths.append(len(tokens))
            for token in set(tokens):
                self.doc_freq[token] += 1
        self.avgdl = sum(lengths) / max(1, len(lengths))

    def search(self, query: str, top_k=8):
        q = tokenize(query)
        scores = []
        n = max(1, len(self.doc_tokens))
        for idx, freqs in enumerate(self.doc_tokens):
            score = 0.0
            dl = sum(freqs.values()) or 1
            for token in q:
                if token not in freqs:
                    continue
                idf = math.log(1 + (n - self.doc_freq[token] + 0.5) / (self.doc_freq[token] + 0.5))
                tf = freqs[token]
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            if score > 0:
                scores.append((self.chunks[idx]["chunk_id"], score))
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
