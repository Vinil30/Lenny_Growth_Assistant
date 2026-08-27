import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


FRONT_MATTER_RE = re.compile(r"^---\s*(.*?)\s*---\s*", re.S)
TURN_RE = re.compile(r"^\*\*(?P<speaker>.+?)\*\*\s*\((?P<time>[^)]+)\):\s*$")


@dataclass
class Turn:
    episode_id: str
    turn_index: int
    speaker: str
    timestamp: str
    text: str


@dataclass
class Episode:
    episode_id: str
    path: str
    metadata: dict
    turns: list[Turn]


def parse_front_matter(raw: str) -> tuple[dict, str]:
    match = FRONT_MATTER_RE.match(raw)
    if not match:
        return {}, raw
    metadata = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, raw[match.end() :]


def parse_turns(body: str, episode_id: str) -> list[Turn]:
    turns = []
    current = None
    chunks = []
    for line in body.splitlines():
        match = TURN_RE.match(line.strip())
        if match:
            if current:
                turns.append(Turn(episode_id, len(turns), current["speaker"], current["timestamp"], "\n".join(chunks).strip()))
            current = {"speaker": match.group("speaker").strip(), "timestamp": match.group("time").strip()}
            chunks = []
        elif current:
            chunks.append(line.strip())
    if current:
        turns.append(Turn(episode_id, len(turns), current["speaker"], current["timestamp"], "\n".join(chunks).strip()))
    return [t for t in turns if t.text]


def parse_episode(path: Path) -> Episode:
    raw = path.read_text(encoding="utf-8")
    metadata, body = parse_front_matter(raw)
    episode_id = metadata.get("video_id") or path.stem
    metadata.setdefault("episode_id", episode_id)
    metadata.setdefault("source_file", str(path))
    return Episode(episode_id=episode_id, path=str(path), metadata=metadata, turns=parse_turns(body, episode_id))


def parse_episodes(transcript_dir: str) -> list[Episode]:
    return [parse_episode(path) for path in sorted(Path(transcript_dir).glob("*.md"))]


def episode_to_dict(episode: Episode) -> dict:
    return {"episode_id": episode.episode_id, "path": episode.path, "metadata": episode.metadata, "turns": [asdict(t) for t in episode.turns]}
