from unittest.mock import Mock

import pytest
from qdrant_client import QdrantClient
from test_coach import draft
from test_documents import resource
from test_ingestion import FakeEncoder

from nexusmind.application.coach import Coach
from nexusmind.application.retrieval import Retriever
from nexusmind.application.scout import ScoutAgent
from nexusmind.domain.documents import normalize
from nexusmind.domain.knowledge import SourceArticle
from nexusmind.domain.retrieval import Passage, RetrievalRequest, RetrievalResult
from nexusmind.infrastructure.storage import Catalog
from nexusmind.infrastructure.vector_store import VectorStore


def article(**changes):
    return SourceArticle(
        **{
            "source_id": "test-guide",
            "source_key": "waves",
            "source_name": "Synthetic guide",
            "source_url": "https://example.org/guide",
            "source_revision": "r1",
            "title": "Gestion de vague",
            "locale": "fr_FR",
            "patch": "unversioned",
            "license_name": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "attribution": "Synthetic fixture, not a game reference",
            "retrieved_at": "2026-11-01T12:00:00+00:00",
            "topics": ["freeze", "vague"],
            "sections": {
                "Observation": "Texte synthétique sur le freeze, pour vérifier le routage."
            },
            **changes,
        }
    )


@pytest.fixture
def pipeline(tmp_path):
    client = QdrantClient(":memory:")
    catalog = Catalog(tmp_path / "catalog.sqlite")
    encoder = FakeEncoder()
    store = VectorStore(client, encoder)
    scout = ScoutAgent(Mock(), encoder, store, catalog, tmp_path / "raw")
    yield scout, catalog, store, encoder
    catalog.close()
    client.close()


def test_reference_replay_is_stable_and_source_revision_is_immutable(pipeline):
    scout, catalog, store, _ = pipeline
    first = scout.ingest_articles([article()])
    second = scout.ingest_articles([article()])
    assert first.status == second.status == "completed"
    assert store.count() == catalog.document_count() == 1
    with pytest.raises(ValueError, match="revision"):
        scout.ingest_articles([article(sections={"Other": "Changed content"})])
    assert catalog.latest_run()["status"] == "failed"


def test_index_failure_does_not_activate_partial_reference_revision(pipeline):
    scout, catalog, store, _ = pipeline
    scout.ingest_articles([article()])
    store.upsert = Mock(side_effect=RuntimeError("index down"))
    with pytest.raises(RuntimeError):
        scout.ingest_articles([article(source_revision="r2")])
    assert {doc.source_revision for doc in catalog.documents()} == {"r1"}


def test_newest_reference_is_routed_with_real_patch_and_license(pipeline):
    scout, catalog, store, _ = pipeline
    scout.ingest_articles(
        [
            article(),
            article(
                source_revision="r2",
                retrieved_at="2026-11-01T13:00:00+00:00",
                sections={"Observation": "Nouvelle édition synthétique sur le freeze."},
            ),
        ]
    )
    result = Retriever(store, catalog.documents()).retrieve(
        RetrievalRequest(query="Comment freeze une vague ?", patch="16.21.1")
    )
    assert result.status == "ok" and len(result.passages) == 1
    assert result.passages[0].source_revision == "r2"
    assert result.passages[0].patch == "unversioned"
    assert result.passages[0].license_name == "CC BY 4.0"
    assert any("non versionn" in text for text in result.limitations)
    assert result.filters.entity_type == "concept"


def test_static_route_keeps_priority_and_unsupported_claims_stay_out_of_scope(pipeline):
    scout, catalog, store, encoder = pipeline
    docs = normalize(resource())
    store.upsert(docs, encoder.encode([doc.text for doc in docs]))
    catalog.save_documents(docs)
    scout.ingest_articles([article(topics=["Ahri", "freeze"])])
    retriever = Retriever(store, catalog.documents())
    factual = retriever.retrieve(RetrievalRequest(query="Passif de Ahri", patch="16.1.1"))
    assert factual.status == "ok"
    assert all(doc.source_name == "Riot Data Dragon" for doc in factual.passages)
    unsupported = retriever.retrieve(
        RetrievalRequest(query="Quel est le winrate de Ahri ?", patch="16.1.1")
    )
    assert unsupported.status == "out_of_scope"


def test_reference_language_and_patch_do_not_fall_back_silently(pipeline):
    scout, catalog, store, _ = pipeline
    scout.ingest_articles([article(patch="16.20", locale="en_US")])
    result = Retriever(store, catalog.documents()).retrieve(
        RetrievalRequest(query="freeze", patch="16.21.1", corpus="reference")
    )
    assert result.status == "no_results" and not result.passages


def test_reference_search_outage_is_not_absence(pipeline):
    scout, catalog, store, _ = pipeline
    scout.ingest_articles([article()])
    store.search = Mock(side_effect=RuntimeError("offline"))
    result = Retriever(store, catalog.documents()).retrieve(
        RetrievalRequest(query="freeze", patch="16.21.1")
    )
    assert result.status == "unavailable"


def test_reference_route_respects_explicit_static_filters(pipeline):
    scout, catalog, store, _ = pipeline
    scout.ingest_articles([article()])
    result = Retriever(store, catalog.documents()).retrieve(
        RetrievalRequest(query="freeze", patch="16.21.1", entity_type="champion")
    )
    assert result.status != "ok" and not result.passages
    static = Retriever(store, catalog.documents()).retrieve(
        RetrievalRequest(query="freeze", patch="16.21.1", entity_type="concept", corpus="static")
    )
    assert static.status != "ok" and not static.passages


def test_reference_client_query_selects_requested_ability_before_ranking(pipeline):
    scout, catalog, store, _ = pipeline
    scout.ingest_articles(
        [
            article(
                source_id="communitydragon",
                topics=["Ahri"],
                sections={
                    "Passif — Soin": "Soigne.",
                    "Q — Orbe": "Revient.",
                    "W — Lucioles": "Déplacement.",
                    "E — Charme": "Charme.",
                    "R — Dash": "Dash.",
                },
            )
        ]
    )
    result = Retriever(store, catalog.documents()).retrieve(
        RetrievalRequest(
            query="Comment fonctionne le Q de Ahri ?", patch="16.21.1", corpus="reference"
        )
    )
    assert result.status == "ok"
    assert len(result.passages) == 1 and "Q — Orbe" in result.passages[0].section


def test_failed_later_batch_keeps_the_old_complete_article(pipeline):
    scout, catalog, store, _ = pipeline
    scout.ingest_articles([article()])
    scout.batch_size = 1
    upsert = store.upsert
    attempts = []

    def fail_second(documents, vectors):
        attempts.append(documents)
        if len(attempts) == 2:
            raise RuntimeError("interrupted")
        upsert(documents, vectors)

    store.upsert = fail_second
    with pytest.raises(RuntimeError):
        scout.ingest_articles([article(source_revision="r2", sections={"Long": "word " * 200})])
    assert {doc.source_revision for doc in catalog.documents()} == {"r1"}
    result = Retriever(store, catalog.documents()).retrieve(
        RetrievalRequest(query="freeze", patch="16.21.1")
    )
    assert result.status == "ok" and {p.source_revision for p in result.passages} == {"r1"}


def test_coach_accepts_reference_scope_without_relabeling_it_as_current_patch():
    doc = article().documents()[0]
    passage = Passage(
        **doc.model_dump(), score=0.5, embedding_model="test", embedding_revision="test"
    )
    evidence = RetrievalResult(
        query="freeze",
        patch="16.21.1",
        locale="fr_FR",
        status="ok",
        passages=[passage],
        collection="test",
        elapsed_ms=0,
    )
    generator = Mock(model="test", generate=Mock(return_value=draft(doc.id)))
    result = Coach(generator).respond(evidence)
    assert result.status == "answered"
    assert result.sources[0].patch == "unversioned"
    assert result.sources[0].attribution == doc.attribution


@pytest.mark.parametrize(
    "changes",
    [
        {"topics": [""]},
        {"sections": {"Observation": " "}},
        {"retrieved_at": "2026-11-01T12:00:00"},
        {"source_id": ""},
    ],
)
def test_reference_contract_refuses_missing_provenance_or_content(changes):
    with pytest.raises(ValueError):
        article(**changes)
