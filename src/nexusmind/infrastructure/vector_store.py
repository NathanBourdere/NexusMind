"""One collection per compatible encoder/schema; never recreate existing collections."""

import hashlib
import json

from qdrant_client import QdrantClient, models

from nexusmind.application.ports import Encoder
from nexusmind.domain.documents import Document
from nexusmind.domain.vectors import validate_vectors


class VectorStore:
    def __init__(self, client: QdrantClient, encoder: Encoder, create_indexes: bool = False):
        self.client = client
        self.encoder = encoder
        self.dimension = encoder.dimension
        self.create_indexes = create_indexes
        identity = json.dumps([encoder.model_name, encoder.revision, self.dimension, 1, "max512"])
        suffix = hashlib.sha256(identity.encode()).hexdigest()[:16]
        self.collection = f"nexusmind_knowledge_v1_{suffix}"
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=models.VectorParams(
                    size=self.dimension, distance=models.Distance.COSINE
                ),
            )
        # Payload indexes improve server filtering; local Qdrant scans small corpora.
        if self.create_indexes:
            for field in ("patch", "locale", "entity_type", "entity_id"):
                self.client.create_payload_index(
                    self.collection, field, models.PayloadSchemaType.KEYWORD, wait=True
                )
        config = self.client.get_collection(self.collection).config.params.vectors
        if not isinstance(config, models.VectorParams) or config.size != self.dimension:
            raise ValueError("Existing Qdrant collection has an incompatible vector dimension")
        if config.distance != models.Distance.COSINE:
            raise ValueError("Existing Qdrant collection has an incompatible distance")
        self._initialized = True

    def upsert(self, documents: list[Document], vectors: list[list[float]]) -> None:
        validate_vectors(vectors, len(documents), self.dimension)
        self.initialize()
        self.client.upsert(
            self.collection,
            wait=True,
            points=[
                models.PointStruct(
                    id=doc.id,
                    vector=vector,
                    payload={
                        **doc.model_dump(),
                        "embedding_model": self.encoder.model_name,
                        "embedding_revision": self.encoder.revision,
                    },
                )
                for doc, vector in zip(documents, vectors, strict=True)
            ],
        )

    def count(self) -> int:
        if not self.client.collection_exists(self.collection):
            return 0
        return self.client.count(self.collection, exact=True).count

    def search(self, query: str, *, patch: str, locale: str, limit: int = 5) -> list[dict]:
        if not self.client.collection_exists(self.collection):
            raise ValueError("Knowledge collection does not exist; run ingestion first")
        self.initialize()
        vectors = self.encoder.encode([query])
        validate_vectors(vectors, 1, self.dimension)
        condition = models.Filter(
            must=[
                models.FieldCondition(key=key, match=models.MatchValue(value=value))
                for key, value in (("patch", patch), ("locale", locale))
            ]
        )
        hits = self.client.query_points(
            self.collection,
            query=vectors[0],
            query_filter=condition,
            limit=limit,
            with_payload=True,
        ).points
        return [{"id": str(hit.id), "score": hit.score, "payload": hit.payload} for hit in hits]
