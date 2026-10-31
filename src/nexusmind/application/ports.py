"""The application depends on contracts, not database or model SDKs."""

from collections.abc import Iterable
from typing import Any, Protocol

from nexusmind.domain.documents import Document


class Source(Protocol):
    def resolve_patch(self, patch: str | None) -> str: ...
    def collect(
        self, patch: str, locale: str, kinds: list[str], champions: list[str] | None = None
    ) -> Iterable[dict[str, Any]]: ...


class Encoder(Protocol):
    model_name: str
    revision: str

    @property
    def dimension(self) -> int: ...
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class Index(Protocol):
    collection: str

    def upsert(self, documents: list[Document], vectors: list[list[float]]) -> None: ...


class DocumentCatalog(Protocol):
    def start_run(self, run_id: str, metadata: dict) -> None: ...
    def save_documents(self, documents: list[Document]) -> None: ...
    def finish_run(self, report: dict) -> None: ...
