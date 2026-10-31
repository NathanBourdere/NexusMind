"""Synchronous, replayable ingestion. No autonomous LLM or legacy scraper calls."""

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from nexusmind.application.ports import DocumentCatalog, Encoder, Index, Source
from nexusmind.domain.documents import normalize
from nexusmind.domain.vectors import validate_vectors


@dataclass
class IngestionReport:
    run_id: str
    status: str
    started_at: str
    patch: str | None
    locale: str
    collection: str
    resources: int = 0
    documents: int = 0
    completed_at: str | None = None
    error: str | None = None


class ScoutAgent:
    def __init__(
        self,
        source: Source,
        encoder: Encoder,
        store: Index,
        catalog: DocumentCatalog,
        raw_dir: Path,
        batch_size: int = 32,
    ):
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self.source = source
        self.encoder = encoder
        self.store = store
        self.catalog = catalog
        self.raw_dir = raw_dir
        self.batch_size = batch_size

    def ingest(
        self,
        *,
        locale: str,
        kinds: list[str],
        patch: str | None = None,
        champions: list[str] | None = None,
    ) -> IngestionReport:
        report = IngestionReport(
            str(uuid.uuid4()),
            "running",
            datetime.now(UTC).isoformat(),
            patch,
            locale,
            self.store.collection,
        )
        self.catalog.start_run(report.run_id, asdict(report))
        try:
            report.patch = self.source.resolve_patch(patch)
            for resource in self.source.collect(report.patch, locale, kinds, champions):
                self._archive(resource)
                documents = normalize(resource)
                report.resources += 1
                for start in range(0, len(documents), self.batch_size):
                    batch = documents[start : start + self.batch_size]
                    vectors = self.encoder.encode([doc.text for doc in batch])
                    validate_vectors(vectors, len(batch), self.encoder.dimension)
                    self.store.upsert(batch, vectors)
                    # A replay reconciles the stores if this commit fails after Qdrant upsert.
                    self.catalog.save_documents(batch)
                    report.documents += len(batch)
            if report.resources == 0:
                raise ValueError("No resources collected")
            report.status = "completed"
        except Exception as exc:
            report.status = "failed"
            report.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            report.completed_at = datetime.now(UTC).isoformat()
            self.catalog.finish_run(asdict(report))
        return report

    def _archive(self, resource: dict) -> None:
        # Hash both URL and data, but not the collection time: identical replays reuse the archive.
        body = json.dumps(
            [resource["source_url"], resource["data"]], sort_keys=True, ensure_ascii=False
        )
        key = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        path = self.raw_dir / f"{key}.json"
        if not path.exists():
            temporary = path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(resource, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporary.replace(path)
