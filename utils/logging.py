import json
import logging
import time
from contextlib import contextmanager


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_event(event: str, **fields) -> None:
    safe = {k: v for k, v in fields.items() if "key" not in k.lower() and "prompt" not in k.lower()}
    logging.info(json.dumps({"event": event, **safe}, default=str))


@contextmanager
def timed(timings: dict, name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        timings[f"{name}_ms"] = round((time.perf_counter() - start) * 1000, 2)
