from unittest.mock import Mock

import pytest
from test_documents import resource

from nexusmind.application.coach import Coach
from nexusmind.domain.coaching import (
    CoachDraft,
    InvalidGeneration,
    ProviderUnavailable,
    QuotaExceeded,
)
from nexusmind.domain.documents import normalize
from nexusmind.domain.retrieval import Passage, RetrievalResult


def evidence(status="ok"):
    doc = normalize(resource())[0]
    return RetrievalResult(
        query="Décris Ahri",
        patch=doc.patch,
        locale=doc.locale,
        status=status,
        passages=[
            Passage(
                **doc.model_dump(), score=0.8, embedding_model="test", embedding_revision="test"
            )
        ],
        collection="test",
        elapsed_ms=0,
    )


def draft(ref):
    return CoachDraft(
        status="answered",
        claims=[
            {
                "kind": "sourced_fact",
                "text": "Description tirée du passage.",
                "evidence_ids": [ref],
            }
        ],
        exercise="Relis la description en jeu.",
        limitations=[],
    )


@pytest.mark.parametrize(
    "status", ["needs_clarification", "out_of_scope", "no_results", "unavailable"]
)
def test_non_ok_retrieval_never_calls_llm(status):
    generator = Mock(model="test")
    result = Coach(generator).respond(evidence(status))
    assert result.status == status
    assert not result.claims
    generator.generate.assert_not_called()


def test_answer_preserves_real_citations_and_provenance():
    passages = evidence()
    generator = Mock(model="test", generate=Mock(return_value=draft(passages.passages[0].id)))
    result = Coach(generator).respond(passages, level="advanced")
    assert result.status == "answered"
    assert result.sources == passages.passages
    assert result.sources[0].source_url == passages.passages[0].source_url
    assert result.sources[0].retrieved_at == passages.passages[0].retrieved_at
    generator.generate.assert_called_once_with(passages, "advanced")


def test_invented_citation_rejects_entire_answer():
    generator = Mock(model="test", generate=Mock(return_value=draft("invented")))
    result = Coach(generator).respond(evidence())
    assert result.status == "invalid_generation"
    assert not result.claims and not result.sources and not result.exercise


def test_failure_has_no_retry_or_secret_leak():
    generator = Mock(model="test", generate=Mock(side_effect=RuntimeError("SECRET")))
    result = Coach(generator).respond(evidence())
    assert result.status == "unavailable"
    assert "SECRET" not in result.model_dump_json()
    generator.generate.assert_called_once()


def test_llm_abstention_discards_claims():
    response = draft("anything").model_copy(update={"status": "insufficient_evidence"})
    generator = Mock(model="test", generate=Mock(return_value=response))
    result = Coach(generator).respond(evidence())
    assert result.status == "insufficient_evidence"
    assert not result.claims and not result.exercise


@pytest.mark.parametrize("change", [{"patch": "1.1.1"}, {"locale": "en_US"}, {"text": "x" * 8001}])
def test_invalid_context_never_calls_llm(change):
    passages = evidence()
    passages.passages = [passages.passages[0].model_copy(update=change)]
    generator = Mock(model="test")
    assert Coach(generator).respond(passages).status == "invalid_generation"
    generator.generate.assert_not_called()


@pytest.mark.parametrize(
    "error,status",
    [
        (QuotaExceeded(), "quota_exceeded"),
        (InvalidGeneration(), "invalid_generation"),
    ],
)
def test_generation_failure_categories_are_distinct(error, status):
    generator = Mock(model="test", generate=Mock(side_effect=error))
    assert Coach(generator).respond(evidence()).status == status


def test_provider_error_exposes_only_safe_diagnostics():
    generator = Mock(model="test", generate=Mock(side_effect=ProviderUnavailable(status_code=403)))
    result = Coach(generator).respond(evidence())
    assert result.status == "unavailable"
    assert result.provider_status == 403
    assert result.provider_error == "http"
