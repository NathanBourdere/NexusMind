"""Explicit model loading; failures propagate and never produce fallback vectors."""

import re

from nexusmind.domain.vectors import validate_vectors

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_REVISION = "86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d"


class SentenceEncoder:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        revision: str = DEFAULT_REVISION,
        *,
        offline: bool = False,
        cache_folder: str | None = None,
    ):
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("An immutable 40-character model revision is required")
        self.model_name = model_name
        self.revision = revision
        self.offline = offline
        self.cache_folder = cache_folder
        self._model = None

    def _load(self):
        if self._model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            # Bound CPU parallelism for predictable local inference and responsive tooling.
            torch.set_num_threads(4)
            self._model = SentenceTransformer(
                self.model_name,
                revision=self.revision,
                device="cpu",
                local_files_only=self.offline,
                cache_folder=self.cache_folder,
                trust_remote_code=False,
            )
            self._model.max_seq_length = 512
        return self._model

    @property
    def dimension(self) -> int:
        dimension = self._load().get_embedding_dimension()
        if dimension is None or dimension <= 0:
            raise ValueError("Model did not provide a valid embedding dimension")
        return dimension

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError("Cannot encode empty passages")
        tokenized = self._load().tokenizer(texts, truncation=False, padding=False)
        if any(len(tokens) > 512 for tokens in tokenized["input_ids"]):
            raise ValueError("Passage exceeds the 512-token budget; rechunk instead of truncating")
        vectors = (
            self._load()
            .encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
            .tolist()
        )
        validate_vectors(vectors, len(texts), self.dimension)
        return vectors
