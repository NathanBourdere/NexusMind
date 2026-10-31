from unittest.mock import Mock

import pytest

from nexusmind.infrastructure.embeddings import SentenceEncoder


def test_model_load_failure_is_propagated_without_fallback(monkeypatch):
    encoder = SentenceEncoder(offline=True)
    monkeypatch.setattr(encoder, "_load", Mock(side_effect=RuntimeError("model unavailable")))
    with pytest.raises(RuntimeError, match="model unavailable"):
        encoder.encode(["Ahri"])


def test_oversized_passages_are_rejected_before_encoding():
    encoder = SentenceEncoder()
    model = Mock()
    model.tokenizer.return_value = {"input_ids": [list(range(513))]}
    encoder._model = model
    with pytest.raises(ValueError, match="rechunk"):
        encoder.encode(["long passage"])
    model.encode.assert_not_called()


def test_mutable_model_revision_is_rejected():
    with pytest.raises(ValueError, match="immutable"):
        SentenceEncoder(revision="main")
