from dataclasses import dataclass, asdict
from typing import Iterable

import numpy as np

from .parsing import Episode, Turn


@dataclass
class Chunk:
    chunk_id: str
    episode_id: str
    segment_id: str
    turn_start: int
    turn_end: int
    speakers: list[str]
    text: str
    embedding_text: str
    metadata: dict


def _turn_text(turn: Turn) -> str:
    return f"{turn.speaker}: {turn.text}"


def semantic_segments(episode: Episode, embedder, min_turns=4, max_turns=18, window=3, threshold=0.42) -> list[tuple[int, int]]:
    turns = episode.turns
    if not turns:
        return []
    windows = ["\n".join(_turn_text(t) for t in turns[i : i + window]) for i in range(max(1, len(turns) - window + 1))]
    vectors = embedder.encode(windows)
    cuts = [0]
    for i in range(1, len(vectors)):
        if i - cuts[-1] < min_turns:
            continue
        sim = float(np.dot(vectors[i - 1], vectors[i]))
        if sim < threshold or i - cuts[-1] >= max_turns:
            cuts.append(i)
    cuts.append(len(turns))
    segments = []
    for start, end in zip(cuts, cuts[1:]):
        if segments and end - start < min_turns:
            old_start, _ = segments.pop()
            segments.append((old_start, end))
        else:
            segments.append((start, end))
    return segments


def make_chunks(episodes: Iterable[Episode], embedder, max_chars=3600, overlap_turns=2) -> list[Chunk]:
    chunks = []
    for episode in episodes:
        segments = semantic_segments(episode, embedder)
        for seg_idx, (start, end) in enumerate(segments):
            i = start
            part = 0
            while i < end:
                selected = []
                char_count = 0
                j = i
                while j < end:
                    text = _turn_text(episode.turns[j])
                    if selected and char_count + len(text) > max_chars:
                        break
                    selected.append(episode.turns[j])
                    char_count += len(text)
                    j += 1
                speakers = sorted({t.speaker for t in selected})
                dialogue = "\n".join(_turn_text(t) for t in selected)
                title = episode.metadata.get("title", episode.episode_id)
                summary = f"Episode: {title}. Guest: {episode.metadata.get('guest', 'Unknown')}."
                chunk_id = f"{episode.episode_id}:s{seg_idx}:c{part}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        episode_id=episode.episode_id,
                        segment_id=f"{episode.episode_id}:s{seg_idx}",
                        turn_start=selected[0].turn_index,
                        turn_end=selected[-1].turn_index,
                        speakers=speakers,
                        text=dialogue,
                        embedding_text=f"{summary}\n{dialogue}",
                        metadata=dict(episode.metadata),
                    )
                )
                if j >= end:
                    break
                i = max(i + 1, j - overlap_turns)
                part += 1
    return chunks


def chunk_to_dict(chunk: Chunk) -> dict:
    return asdict(chunk)
