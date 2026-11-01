from unittest.mock import Mock

import pytest
from test_coach import draft, evidence
from test_documents import resource

from nexusmind.application.coach_evaluation import evaluate_coach
from nexusmind.domain.coaching import QuotaExceeded
from nexusmind.domain.documents import normalize
from nexusmind.domain.evaluation import EvaluationSuite


def suite():
    return EvaluationSuite(
        name="test",
        patch="16.1.1",
        locale="fr_FR",
        cases=[
            {
                "id": str(i),
                "split": "validation",
                "query": "Décris Ahri",
                "expected_status": "ok",
                "expected": [
                    {
                        "entity_type": "champion",
                        "entity_id": "Ahri",
                        "section": "overview",
                    }
                ],
            }
            for i in range(3)
        ],
    )


def test_default_is_a_plan_without_a_provider_call():
    retriever = Mock(retrieve=Mock(return_value=evidence()))
    result = evaluate_coach(suite(), retriever, normalize(resource()))
    assert result["status"] == "planned"
    assert result["calls_attempted"] == 0
    assert len(result["cases"]) == 3
    assert all(row["result"] is None for row in result["cases"])


def test_live_budget_counts_attempts_and_keeps_unrun_cases_visible():
    retriever = Mock(retrieve=Mock(return_value=evidence()))
    generator = Mock(model="test", generate=Mock(return_value=draft(evidence().passages[0].id)))
    result = evaluate_coach(suite(), retriever, normalize(resource()), generator, max_calls=1)
    assert result["status"] == "partial"
    assert result["calls_attempted"] == 1
    assert [row["execution"] for row in result["cases"]] == ["completed", "not_run", "not_run"]
    assert result["cases"][0]["human_review"]["facts_supported"] is None
    generator.generate.assert_called_once()


def test_quota_stops_the_run_without_retry():
    generator = Mock(model="test", generate=Mock(side_effect=QuotaExceeded()))
    result = evaluate_coach(
        suite(), Mock(retrieve=Mock(return_value=evidence())), normalize(resource()), generator
    )
    assert result["status"] == "stopped"
    assert result["stop_reason"] == "quota_exceeded"
    generator.generate.assert_called_once()
    assert len(result["cases"]) == 3


def test_missing_gold_fails_before_retrieval_or_generation():
    retriever = Mock()
    with pytest.raises(ValueError, match="Missing gold"):
        evaluate_coach(suite(), retriever, [], Mock())
    retriever.retrieve.assert_not_called()


def test_abstention_does_not_consume_generation_budget():
    cases = suite()
    cases.cases[0] = cases.cases[0].model_copy(
        update={
            "expected_status": "out_of_scope",
            "expected": [],
        }
    )
    retriever = Mock(retrieve=Mock(side_effect=[evidence("out_of_scope"), evidence(), evidence()]))
    generator = Mock(model="test", generate=Mock(return_value=draft(evidence().passages[0].id)))
    result = evaluate_coach(cases, retriever, normalize(resource()), generator, max_calls=1)
    assert result["cases"][0]["result"]["status"] == "out_of_scope"
    assert result["cases"][1]["result"]["status"] == "answered"
    assert result["calls_attempted"] == 1


def test_live_evaluation_spaces_provider_calls_with_injected_sleep():
    generator = Mock(model="test", generate=Mock(return_value=draft(evidence().passages[0].id)))
    pause = Mock()
    result = evaluate_coach(
        suite(),
        Mock(retrieve=Mock(return_value=evidence())),
        normalize(resource()),
        generator,
        call_interval=5,
        sleep=pause,
    )
    assert result["status"] == "completed"
    assert result["call_interval_seconds"] == 5
    assert [call.args[0] for call in pause.call_args_list] == [5, 5]
