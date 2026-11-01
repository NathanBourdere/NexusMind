"""Plan and run a bounded coaching evaluation without an LLM judge."""

import hashlib
import json
import math
from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from time import sleep as default_sleep

from nexusmind.application.coach import Coach, Generator
from nexusmind.application.evaluation import resolve_gold
from nexusmind.application.retrieval import Retriever
from nexusmind.domain.documents import Document
from nexusmind.domain.evaluation import EvaluationSuite


class _CountedGenerator:
    def __init__(self, generator: Generator):
        self.generator = generator
        self.model = generator.model
        self.calls = 0

    def generate(self, evidence, level):
        self.calls += 1
        return self.generator.generate(evidence, level)


def evaluate_coach(
    suite: EvaluationSuite,
    retriever: Retriever,
    documents: list[Document],
    generator: Generator | None = None,
    *,
    max_calls: int = 3,
    level: str = "beginner",
    call_interval: float = 0,
    sleep: Callable[[float], None] = default_sleep,
) -> dict:
    if not 1 <= max_calls <= 30:
        raise ValueError("max-calls must be between 1 and 30")
    if level not in {"beginner", "intermediate", "advanced"}:
        raise ValueError("Unknown coaching level")
    if not math.isfinite(call_interval) or not 0 <= call_interval <= 60:
        raise ValueError("call-interval must be between 0 and 60 seconds")
    gold = {case.id: resolve_gold(case, suite.request_for(case), documents) for case in suite.cases}
    # Resolve the entire plan first: no API call if any retrieval is unavailable.
    evidence = [retriever.retrieve(suite.request_for(case)) for case in suite.cases]
    rows = [
        {
            "id": case.id,
            "split": case.split,
            "query": case.query,
            "expected_status": "answered" if case.expected_status == "ok" else case.expected_status,
            "gold_ids": gold[case.id],
            "retrieval": found.model_dump(),
            "execution": "planned" if generator is None else "not_run",
            "result": None,
            "elapsed_ms": None,
            "status_matches_expected": None,
            "human_review": {
                "facts_supported": None,
                "no_invented_numbers": None,
                "pedagogy_useful": None,
                "notes": "",
            },
        }
        for case, found in zip(suite.cases, evidence, strict=True)
    ]
    counted = _CountedGenerator(generator) if generator is not None else None
    stop = "retrieval_unavailable" if any(e.status == "unavailable" for e in evidence) else None
    if counted is not None and stop is None:
        coach = Coach(counted)
        for row, found in zip(rows, evidence, strict=True):
            if found.status == "ok" and counted.calls >= max_calls:
                continue
            if found.status == "ok" and counted.calls and call_interval:
                sleep(call_interval)
            start = perf_counter()
            result = coach.respond(found, level=level)
            row.update(
                execution="completed",
                result=result.model_dump(),
                elapsed_ms=round((perf_counter() - start) * 1000, 3),
                status_matches_expected=result.status == row["expected_status"],
            )
            if result.status in {"quota_exceeded", "unavailable", "invalid_generation"}:
                stop = result.status
                break
    status = (
        "stopped"
        if stop
        else (
            "planned"
            if counted is None
            else "partial"
            if any(row["execution"] == "not_run" for row in rows)
            else "completed"
        )
    )
    return {
        "schema_version": 1,
        "status": status,
        "stop_reason": stop,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "suite": suite.name,
        "suite_fingerprint": hashlib.sha256(suite.model_dump_json().encode()).hexdigest(),
        "corpus_fingerprint": hashlib.sha256(
            json.dumps(sorted((doc.id, doc.content_hash) for doc in documents)).encode()
        ).hexdigest(),
        "level": level,
        "model": counted.model if counted else None,
        "max_calls": max_calls,
        "call_interval_seconds": call_interval,
        "calls_attempted": counted.calls if counted else 0,
        "cases": rows,
        "limitations": [
            "Retrieval labels are provisional generation expectations, not semantic gold.",
            "Status matches do not measure correctness or pedagogy; human review is required.",
            "No LLM judge, automatic retry, or paid fallback. Unrun cases remain visible.",
            "Latency excludes loading and retrieval. Model identifier may be a provider alias.",
        ],
    }
