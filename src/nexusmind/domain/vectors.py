import math


def validate_vectors(vectors: list[list[float]], count: int, dimension: int) -> None:
    if len(vectors) != count:
        raise ValueError("Encoder output count does not match input count")
    for vector in vectors:
        if len(vector) != dimension:
            raise ValueError("Embedding dimension mismatch")
        if not all(math.isfinite(value) for value in vector):
            raise ValueError("Embedding contains a non-finite value")
        if not any(value != 0 for value in vector):
            raise ValueError("Zero embeddings cannot be indexed or searched")
