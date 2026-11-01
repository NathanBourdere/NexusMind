import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from test_documents import resource

from nexusmind.application.evaluation import evaluate, metrics, resolve_gold
from nexusmind.domain.documents import normalize
from nexusmind.domain.evaluation import EvaluationSuite


def test_recall_and_mrr_count_all_gold_and_deduplicate_hits():
    rows = [
        {
            "gold": ["a", "b"],
            "ids": ["x", "a", "a"],
            "expected_status": "ok",
            "status": "ok",
            "elapsed_ms": 2,
        },
        {"gold": ["c"], "ids": ["c"], "expected_status": "ok", "status": "ok", "elapsed_ms": 4},
        {
            "gold": [],
            "ids": [],
            "expected_status": "out_of_scope",
            "status": "out_of_scope",
            "elapsed_ms": 1,
        },
    ]
    result = metrics(rows)
    assert result["recall_at_5"] == 0.75
    assert result["mrr_at_5"] == 0.75
    assert result["abstention_accuracy"] == 1.0
    assert result["positive_cases"] == 2


def test_gold_missing_from_snapshot_fails_instead_of_skipping():
    suite = EvaluationSuite.model_validate(
        {
            "name": "test",
            "patch": "16.1.1",
            "locale": "fr_FR",
            "cases": [
                {
                    "id": "missing",
                    "split": "development",
                    "query": "Ahri",
                    "expected_status": "ok",
                    "expected": [
                        {"entity_type": "champion", "entity_id": "missing", "section": "passive"}
                    ],
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="Missing gold"):
        resolve_gold(suite.cases[0], suite.request_for(suite.cases[0]), normalize(resource()))


def test_negative_case_cannot_contain_gold():
    with pytest.raises(ValueError):
        EvaluationSuite.model_validate(
            {
                "name": "test",
                "patch": "16.1.1",
                "locale": "fr_FR",
                "cases": [
                    {
                        "id": "invalid",
                        "split": "validation",
                        "query": "Ahri",
                        "expected_status": "out_of_scope",
                        "expected": [
                            {"entity_type": "champion", "entity_id": "Ahri", "section": "passive"}
                        ],
                    }
                ],
            }
        )


def test_versioned_suite_has_coverage_and_both_splits():
    path = Path(__file__).resolve().parents[1] / "evaluation/retrieval-v1.json"
    suite = EvaluationSuite.model_validate_json(path.read_text("utf-8"))
    assert len(suite.cases) >= 20
    for split in ("development", "validation"):
        cases = [case for case in suite.cases if case.split == split]
        assert any(case.expected_status == "ok" for case in cases)
        assert any(case.expected_status != "ok" for case in cases)


def test_published_report_is_bound_to_the_exact_suite_and_includes_every_case():
    root = Path(__file__).resolve().parents[1]
    suite = EvaluationSuite.model_validate_json(
        (root / "evaluation/retrieval-v1.json").read_text("utf-8")
    )
    report = json.loads((root / "evaluation/reports/riot-static-fr-v1.json").read_text("utf-8"))
    assert (
        report["suite_fingerprint"] == hashlib.sha256(suite.model_dump_json().encode()).hexdigest()
    )
    assert sorted(case["id"] for case in report["cases"]) == sorted(case.id for case in suite.cases)


def test_evaluation_aborts_on_backend_outage_instead_of_reporting_scores():
    suite = EvaluationSuite.model_validate(
        {
            "name": "test",
            "patch": "16.1.1",
            "locale": "fr_FR",
            "cases": [
                {
                    "id": "outage",
                    "split": "development",
                    "query": "Passif de Ahri",
                    "expected_status": "ok",
                    "expected": [
                        {"entity_type": "champion", "entity_id": "Ahri", "section": "passive"}
                    ],
                }
            ],
        }
    )
    docs = normalize(resource())
    store = Mock(collection="test")
    store.search.side_effect = [
        [{"payload": docs[1].model_dump(), "score": 1}],
        RuntimeError("offline"),
    ]
    with pytest.raises(RuntimeError, match="Retrieval unavailable"):
        evaluate(suite, store, docs, {})
