from unittest.mock import Mock

import pytest
from qdrant_client import QdrantClient
from test_documents import resource
from test_ingestion import FakeEncoder

from nexusmind.application.retrieval import Retriever
from nexusmind.domain.documents import normalize
from nexusmind.domain.retrieval import RetrievalRequest
from nexusmind.infrastructure.vector_store import VectorStore


@pytest.fixture
def knowledge():
    docs = normalize(resource())
    other = resource()
    other["data"] = {
        "data": {
            "Lux": {
                "id": "Lux",
                "name": "Lux",
                "title": "Test",
                "tags": ["Mage"],
                "passive": {"name": "Illumination", "description": "Test"},
                "spells": [{"id": "LuxR", "name": "Rayon test", "description": "Test"}],
            }
        }
    }
    docs += normalize(other)
    client = QdrantClient(":memory:")
    encoder = FakeEncoder()
    store = VectorStore(client, encoder)
    store.upsert(docs, encoder.encode([doc.text for doc in docs]))
    yield docs, store
    client.close()


def test_vector_store_filters_entity_and_sections(knowledge):
    _, store = knowledge
    hits = store.search(
        "sort",
        patch="16.1.1",
        locale="fr_FR",
        entity_type="champion",
        entity_ids=["Lux"],
        sections=["spell:LuxR"],
    )
    assert len(hits) == 1
    assert hits[0]["payload"]["entity_id"] == "Lux"
    assert hits[0]["payload"]["section"] == "spell:LuxR"


def test_request_resolves_entity_and_preserves_sources(knowledge):
    docs, store = knowledge
    result = Retriever(store, docs).retrieve(
        RetrievalRequest(query="Quels sont les sorts de AHRI ?", patch="16.1.1")
    )
    assert result.status == "ok"
    assert result.filters.entity_ids == ["Ahri"]
    assert all(p.entity_id == "Ahri" for p in result.passages)
    assert all(p.source_url.startswith("https://ddragon.") for p in result.passages)
    assert result.limitations


def test_passive_request_narrows_to_relevant_section(knowledge):
    docs, store = knowledge
    result = Retriever(store, docs).retrieve(
        RetrievalRequest(query="Décris le passif de Lux", patch="16.1.1")
    )
    assert result.status == "ok"
    assert [p.section for p in result.passages] == ["passive"]


@pytest.mark.parametrize(
    "query",
    [
        "Comment freeze une vague avec Ahri ?",
        "Quel est le winrate de Lux ?",
        "Analyse ma dernière partie avec Ahri",
        "Quel est le meilleur build de Lux ?",
    ],
)
def test_unsupported_requests_abstain_without_search(knowledge, query):
    docs, store = knowledge
    store.search = Mock()
    result = Retriever(store, docs).retrieve(RetrievalRequest(query=query, patch="16.1.1"))
    assert result.status == "out_of_scope"
    assert result.passages == []
    store.search.assert_not_called()


def test_unknown_entity_requires_clarification(knowledge):
    docs, store = knowledge
    result = Retriever(store, docs).retrieve(
        RetrievalRequest(query="Explique un sort", patch="16.1.1")
    )
    assert result.status == "needs_clarification"
    assert not result.passages


def test_failure_is_distinct_from_no_results(knowledge):
    docs, store = knowledge
    store.search = Mock(side_effect=RuntimeError("embedding unavailable"))
    result = Retriever(store, docs).retrieve(
        RetrievalRequest(query="Sorts de Ahri", patch="16.1.1")
    )
    assert result.status == "unavailable"
    assert result.error_type == "RuntimeError"
    assert not result.passages


def test_filters_do_not_fall_back_to_other_patch(knowledge):
    docs, store = knowledge
    result = Retriever(store, docs).retrieve(
        RetrievalRequest(
            query="Passif de Ahri", patch="16.2.1", entity_type="champion", entity_ids=["Ahri"]
        )
    )
    assert result.status == "no_results"
    assert not result.passages


def test_ambiguous_query_requires_explicit_selection(knowledge):
    docs, store = knowledge
    result = Retriever(store, docs).retrieve(
        RetrievalRequest(query="Compare Ahri et Lux", patch="16.1.1")
    )
    assert result.status == "needs_clarification"


def test_explicit_filter_conflicting_with_named_entity_does_not_return_wrong_facts(knowledge):
    docs, store = knowledge
    result = Retriever(store, docs).retrieve(
        RetrievalRequest(query="Décris le passif de Ahri", patch="16.1.1", entity_ids=["Lux"])
    )
    assert result.status == "needs_clarification"
    assert not result.passages


def test_shared_item_names_require_id_and_explicit_id_resolves_them():
    docs = normalize(
        resource(
            kind="item",
            data={
                "data": {
                    "1001": {"name": "Bottes test", "description": "Version normale"},
                    "771001": {"name": "Bottes test", "description": "Autre variante"},
                }
            },
        )
    )
    client = QdrantClient(":memory:")
    try:
        encoder = FakeEncoder()
        store = VectorStore(client, encoder)
        store.upsert(docs, encoder.encode([doc.text for doc in docs]))
        retriever = Retriever(store, docs)
        automatic = retriever.retrieve(RetrievalRequest(query="Décris Bottes test", patch="16.1.1"))
        assert automatic.status == "needs_clarification"
        assert {candidate.entity_id for candidate in automatic.candidates} == {"1001", "771001"}
        explicit = retriever.retrieve(
            RetrievalRequest(
                query="Décris Bottes test", patch="16.1.1", entity_type="item", entity_ids=["1001"]
            )
        )
        assert explicit.status == "ok"
        assert [p.entity_id for p in explicit.passages] == ["1001"]
    finally:
        client.close()
