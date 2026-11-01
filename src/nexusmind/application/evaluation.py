"""Reproducible before/after evaluation, without LLM judging or hidden dropped cases."""

import hashlib
import json
import math
from datetime import UTC, datetime
from statistics import mean, median
from time import perf_counter

from nexusmind.application.ports import SearchIndex
from nexusmind.application.retrieval import Retriever
from nexusmind.domain.documents import Document
from nexusmind.domain.evaluation import EvaluationCase, EvaluationSuite
from nexusmind.domain.retrieval import RetrievalRequest


def metrics(rows: list[dict]) -> dict:
    positives = [row for row in rows if row["expected_status"] == "ok"]
    negatives = [row for row in rows if row["expected_status"] != "ok"]
    recalls, reciprocal = [], []
    for row in positives:
        ids = list(dict.fromkeys(row["ids"]))[:5]
        gold = set(row["gold"])
        recalls.append(len(set(ids) & gold) / len(gold))
        reciprocal.append(next((1 / rank for rank, item in enumerate(ids, 1) if item in gold), 0))
    timings = sorted(row["elapsed_ms"] for row in rows)
    return {
        "positive_cases": len(positives),
        "negative_cases": len(negatives),
        "recall_at_5": mean(recalls) if recalls else None,
        "mrr_at_5": mean(reciprocal) if reciprocal else None,
        "abstention_accuracy": mean(
            row["status"] == row["expected_status"] and not row["ids"] for row in negatives
        )
        if negatives
        else None,
        "false_evidence_rate": mean(bool(row["ids"]) for row in negatives) if negatives else None,
        "false_abstention_rate": mean(not row["ids"] for row in positives) if positives else None,
        "wrong_entity_hits": sum(row.get("wrong_entity_hits", 0) for row in positives),
        "patch_locale_errors": sum(row.get("patch_locale_errors", 0) for row in rows),
        "latency_p50_ms": median(timings) if timings else None,
        "latency_p95_ms": timings[max(0, math.ceil(len(timings) * 0.95) - 1)] if timings else None,
    }


def resolve_gold(
    case: EvaluationCase, request: RetrievalRequest, documents: list[Document]
) -> list[str]:
    gold = set()
    for selector in case.expected:
        matches = [
            doc.id
            for doc in documents
            if doc.patch == request.patch
            and doc.locale == request.locale
            and doc.entity_type == selector.entity_type
            and doc.entity_id == selector.entity_id
            and (
                doc.section == selector.section
                or doc.section.startswith(selector.section + ":chunk:")
            )
        ]
        if not matches:
            raise ValueError(f"Missing gold passages for case {case.id}: {selector}")
        gold.update(matches)
    return sorted(gold)


def evaluate(
    suite: EvaluationSuite, store: SearchIndex, documents: list[Document], model_metadata: dict
) -> dict:
    # Validate every annotation before any expensive inference; never skip missing gold.
    gold = {case.id: resolve_gold(case, suite.request_for(case), documents) for case in suite.cases}
    retriever = Retriever(store, documents)
    rows = []
    for case in suite.cases:
        request = suite.request_for(case)
        start = perf_counter()
        raw = store.search(request.query, patch=request.patch, locale=request.locale, limit=5)
        raw_time = (perf_counter() - start) * 1000
        improved = retriever.retrieve(request)
        if improved.status == "unavailable":
            raise RuntimeError(
                f"Retrieval unavailable during evaluation: {case.id} ({improved.error_type})"
            )
        targets = {(selector.entity_type, selector.entity_id) for selector in case.expected}

        def row(status, payloads, elapsed, *, case=case, targets=targets, request=request):
            return {
                "gold": gold[case.id],
                "ids": [doc["id"] for doc in payloads],
                "status": status,
                "expected_status": case.expected_status,
                "elapsed_ms": round(elapsed, 3),
                "wrong_entity_hits": sum(
                    (doc["entity_type"], doc["entity_id"]) not in targets for doc in payloads
                )
                if targets
                else 0,
                "patch_locale_errors": sum(
                    doc["patch"] != request.patch or doc["locale"] != request.locale
                    for doc in payloads
                ),
            }

        rows.append(
            {
                "id": case.id,
                "split": case.split,
                "query": case.query,
                "request": request.model_dump(),
                "baseline": row(
                    "ok" if raw else "no_results", [hit["payload"] for hit in raw], raw_time
                ),
                "filtered": row(
                    improved.status,
                    [p.model_dump() for p in improved.passages],
                    improved.elapsed_ms,
                ),
                "filters": improved.filters.model_dump(),
            }
        )
    summaries = {}
    for split in ("all", "development", "validation"):
        subset = rows if split == "all" else [row for row in rows if row["split"] == split]
        if subset:
            summaries[split] = {
                mode: metrics([row[mode] for row in subset]) for mode in ("baseline", "filtered")
            }
    for name, explicit in (("automatic", False), ("explicit_filters", True)):
        subset = [row for row in rows if bool(row["request"]["entity_ids"]) == explicit]
        if subset:
            summaries[name] = {
                mode: metrics([row[mode] for row in subset]) for mode in ("baseline", "filtered")
            }
    fingerprint = hashlib.sha256(
        json.dumps(sorted((doc.id, doc.content_hash) for doc in documents)).encode()
    ).hexdigest()
    return {
        "suite": suite.name,
        "suite_fingerprint": hashlib.sha256(suite.model_dump_json().encode()).hexdigest(),
        "evaluated_at": datetime.now(UTC).isoformat(),
        "corpus": {
            "documents": len(documents),
            "fingerprint": fingerprint,
            "collection": store.collection,
            "patch": suite.patch,
            "locale": suite.locale,
        },
        "model": model_metadata,
        "summaries": summaries,
        "cases": rows,
        "limitations": [
            "Manually authored small suite; not an independent benchmark.",
            "Scores measure passage retrieval, not factual or pedagogical correctness.",
            "Latency excludes model loading; baseline executes first for every case.",
        ],
    }
