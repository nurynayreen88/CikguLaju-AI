"""Pure weekly RPH output progress reconciliation.

Persistence and charging are deliberately delegated to the production transaction layer.
"""
from dataclasses import dataclass
from typing import Mapping, Iterable

ALLOWED = frozenset({"pending", "running", "succeeded", "failed"})

@dataclass(frozen=True)
class JobSummary:
    total: int
    pending: int
    running: int
    succeeded: int
    failed: int
    retry_keys: tuple[str, ...]

def summarize_jobs(keys: Iterable[str], states: Mapping[str, str]) -> JobSummary:
    keys = tuple(keys)
    if len(keys) != len(set(keys)) or any(not key for key in keys):
        raise ValueError("Missing or duplicate job keys")
    if any(key not in keys for key in states):
        raise ValueError("Unexpected job key")
    if any(state not in ALLOWED for state in states.values()):
        raise ValueError("Unknown job state")
    counts = {status: 0 for status in ALLOWED}
    retry = []
    for key in keys:
        status = states.get(key, "pending")
        counts[status] += 1
        if status == "failed":
            retry.append(key)
    return JobSummary(len(keys),counts["pending"],counts["running"],counts["succeeded"],counts["failed"],tuple(retry))

def retry_failed_only(keys: Iterable[str], states: Mapping[str, str]) -> tuple[str, ...]:
    return summarize_jobs(keys,states).retry_keys
