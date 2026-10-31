import json
from unittest.mock import Mock

import pytest
from qdrant_client import QdrantClient
from test_documents import resource

from nexusmind.application.scout import ScoutAgent
from nexusmind.infrastructure.storage import Catalog
from nexusmind.infrastructure.vector_store import VectorStore


class FakeEncoder:
    # Test double only. Production always uses SentenceTransformer.
    model_name = "test-only"
    revision = "0" * 40
    dimension = 3

    def encode(self, texts):
        return [[1.0, 0.5, 0.25] for _ in texts]


@pytest.fixture
def setup(tmp_path):
    catalog = Catalog(tmp_path / "catalog.sqlite")
    client = QdrantClient(":memory:")
    encoder = FakeEncoder()
    store = VectorStore(client=client, encoder=encoder)
    source = Mock()
    source.resolve_patch.return_value = "16.1.1"
    source.collect.side_effect = lambda *args, **kwargs: iter([resource()])
    scout = ScoutAgent(
        source=source,
        encoder=encoder,
        store=store,
        catalog=catalog,
        raw_dir=tmp_path / "raw",
        batch_size=2,
    )
    yield scout, catalog, store, encoder
    client.close()
    catalog.close()


@pytest.mark.integration
def test_full_pipeline_replay_and_filtered_retrieval(setup, tmp_path):
    scout, catalog, store, _ = setup
    first = scout.ingest(locale="fr_FR", kinds=["champion"], champions=["Ahri"])
    second = scout.ingest(locale="fr_FR", kinds=["champion"], champions=["Ahri"])
    assert first.status == second.status == "completed"
    assert first.documents == second.documents == 3
    assert store.count() == 3
    assert catalog.document_count() == 3
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 1
    assert catalog.get_run(second.run_id)["status"] == "completed"
    hits = store.search("orbe", patch="16.1.1", locale="fr_FR", limit=5)
    assert len(hits) == 3
    assert all(hit["payload"]["source_name"] == "Riot Data Dragon" for hit in hits)
    assert store.search("orbe", patch="16.2.1", locale="fr_FR") == []
    archived = json.loads(next((tmp_path / "raw").rglob("*.json")).read_text("utf-8"))
    assert archived["data"] == resource()["data"]


@pytest.mark.parametrize(
    "vectors",
    [
        [[0, 0, 0]] * 2,
        [[1, 2]] * 2,
        [[float("nan"), 0, 1]] * 2,
        [[1, 2, 3]],
    ],
)
def test_bad_embeddings_never_reach_qdrant_and_report_failure(setup, vectors):
    scout, catalog, store, encoder = setup
    encoder.encode = Mock(return_value=vectors)
    with pytest.raises(ValueError):
        scout.ingest(locale="fr_FR", kinds=["champion"])
    assert store.count() == 0
    assert catalog.document_count() == 0
    assert catalog.latest_run()["status"] == "failed"


def test_source_failure_is_not_reported_as_success(setup):
    scout, catalog, _, _ = setup
    scout.source.collect.side_effect = RuntimeError("upstream down")
    with pytest.raises(RuntimeError, match="upstream down"):
        scout.ingest(locale="fr_FR", kinds=["champion"])
    assert catalog.latest_run()["status"] == "failed"


def test_index_error_does_not_record_unindexed_documents(setup):
    scout, catalog, store, _ = setup
    store.upsert = Mock(side_effect=RuntimeError("index unavailable"))
    with pytest.raises(RuntimeError):
        scout.ingest(locale="fr_FR", kinds=["champion"])
    assert catalog.document_count() == 0
    assert catalog.latest_run()["status"] == "failed"


def test_encoder_failure_is_logged_as_failed(setup):
    scout, catalog, store, encoder = setup
    encoder.encode = Mock(side_effect=RuntimeError("model unavailable"))
    with pytest.raises(RuntimeError, match="model unavailable"):
        scout.ingest(locale="fr_FR", kinds=["champion"])
    assert store.count() == 0
    assert catalog.latest_run()["status"] == "failed"


def test_model_revisions_use_separate_collections(setup):
    _, _, store, encoder = setup
    encoder.revision = "1" * 40
    other = VectorStore(client=store.client, encoder=encoder)
    assert other.collection != store.collection
