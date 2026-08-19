"""
Storage + retrieval stage: saves embedded chunks into Milvus Cloud, and
later searches for the chunks closest in meaning to a query vector.
"""
import os
from dotenv import load_dotenv
from pymilvus import MilvusClient
from src.config import COLLECTION_NAME, VECTOR_DIMENSION

# _client = MilvusClient(MILVUS_DB_PATH)

load_dotenv()
 
ZILLIZ_URI = os.getenv("ZILLIZ_URI")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN")
 
# Connecting to Milvus Cloud (Zilliz) instead of a local file
_client = MilvusClient(uri=ZILLIZ_URI, token=ZILLIZ_TOKEN)

def _make_chunk_id(filename: str, idx: int) -> int:
    unique_string = f"{filename}::{idx}"
    return abs(hash(unique_string)) % (10 ** 15)


def reset_collection():
    #drops and recreates the collection useful for clean retesting
    if _client.has_collection(collection_name=COLLECTION_NAME):
        _client.drop_collection(collection_name=COLLECTION_NAME)
    _client.create_collection(
        collection_name=COLLECTION_NAME,
        dimension=VECTOR_DIMENSION,
        metric_type="COSINE",
    )


def insert_chunks(chunks: list, embeddings, filename: str) -> int:
    """
    chunks: list of {"text":..., "source":...}
    embeddings: matching list of vectors (same order, same length)
    filename: the original file's name (e.g. "DSA-GUIDE.pdf") -- stored on
    EVERY chunk so we can later answer "which files are in the store"
    (list) and "delete everything from this one file" (delete).
    Returns the number of rows actually inserted.
    """
    data_to_insert = [
        {
            "id": _make_chunk_id(filename, i),
            "vector": embeddings[i].tolist(),
            "text": chunks[i]["text"],
            "source": chunks[i]["source"],
            "filename": filename,
        }
        for i in range(len(chunks))
    ]
    result = _client.insert(collection_name=COLLECTION_NAME, data=data_to_insert)
    return result["insert_count"]


def search(query_vector, limit: int = 5) -> list:
    """
    Returns the top `limit` chunks closest in meaning to query_vector.
    Each result includes the original text, its source label, its
    filename, and a similarity score.
    """
    _client.load_collection(collection_name=COLLECTION_NAME)

    results = _client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector.tolist()],
        limit=limit,
        output_fields=["text", "source", "filename"],
    )

    retrieved = []
    for hit in results[0]:
        retrieved.append({
            "source": hit["entity"]["source"],
            "text": hit["entity"]["text"],
            "filename": hit["entity"]["filename"],
            "score": hit["distance"],
        })
    return retrieved

def list_files() -> list:
    #simply returns the list of uploaded files, which have chunked and their embeddings are in store
    _client.load_collection(collection_name=COLLECTION_NAME)

    results = _client.query(
        collection_name=COLLECTION_NAME,
        filter="",
        output_fields=["filename"],
        limit=10000,
    )
    filenames = {r["filename"] for r in results}
    return sorted(filenames)

def delete_files(filenames: list) -> list:
    #deleting every chunk belonging to any filename in "filenames" lst
    _client.load_collection(collection_name=COLLECTION_NAME)
    existing_files = set(list_files())
    deleted = []
 
    for filename in filenames:
        if filename not in existing_files:
            continue
        _client.delete(
            collection_name=COLLECTION_NAME,
            filter=f'filename == "{filename}"',
        )
        deleted.append(filename)
 
    return deleted