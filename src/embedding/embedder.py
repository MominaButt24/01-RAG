"""
Embedding stage: turns text into vectors (lists of numbers) that capture
meaning, so "meaning-similar" text ends up as "numerically-similar" vectors.

Loaded once, at import time, because loading the model is slow, don't
want to reload it on every single chunk or every single query.
"""

from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL_NAME

_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_chunks(chunks: list) -> list:
    """
    chunks: list of {"text": ..., "source": ...} dicts (from ingestion).
    Returns: list of embedding vectors, same order as chunks.
    """
    texts = [item["text"] for item in chunks]
    embeddings = _model.encode(texts)
    return embeddings


def embed_query(query: str):
    """
    Embeds a single question. Wrapped in a list ([query]) because the
    model's .encode() always expects a batch/list, even for one item —
    same reason chunk embedding does.
    """
    return _model.encode([query])[0]
