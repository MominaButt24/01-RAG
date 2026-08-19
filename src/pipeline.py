# this is the only file that talks to every stage.
# Nothing outside this file (like main.py) should need to know HOW
# ingestion/embedding/storage/generation work internally


import os

from src.ingestion.file_processor import process_file
from src.embedding.embedder import embed_chunks, embed_query
from src.vectorstore import milvus_store
from src.config import UPLOAD_DIR

def ingest_file(file_path: str) -> int:
    """
    Full ingestion pipeline for ONE file:
    read file -> chunk it -> embed chunks -> store in Milvus, tagged with
    the file's name so it can later be listed or deleted individually.
    Returns how many chunks were stored.
    """
    chunks = process_file(file_path)
    if not chunks:
        return 0

    filename = os.path.basename(file_path)  # e.g. "DSA-GUIDE.pdf" from a full path

    embeddings = embed_chunks(chunks)
    inserted_count = milvus_store.insert_chunks(chunks, embeddings, filename)
    return inserted_count


def ask(query: str, top_k: int = 5) -> dict:
    """
    Full query pipeline:
    embed question -> search Milvus -> generate grounded answer.
    Returns both the answer AND the chunks used, so i can verify it.
    """
    from src.generation.llm import generate_answer  # imported here to avoid
    # loading the Groq client (and requiring an API key) unless someone
    # actually asks a question, ingest_file() alone shouldn't need it.

    query_vector = embed_query(query)
    retrieved_chunks = milvus_store.search(query_vector, limit=top_k)
    answer = generate_answer(query, retrieved_chunks)

    return {"answer": answer, "chunks_used": retrieved_chunks}

def list_uploaded_files() -> list:
    """Returns every filename currently stored and queryable."""
    return milvus_store.list_files()
 
 
def delete_uploaded_files(filenames: list) -> list:
    """
    Deletes all chunks for the given filenames.
    Returns the filenames that were actually found and deleted.
    """
    deleted_from_store = milvus_store.delete_files(filenames)

    for filename in deleted_from_store:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
 
    return deleted_from_store

def reset_everything():
    #restes the store and uploads folder, both clear out 
    milvus_store.reset_collection()
 
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):  # skip subfolders, only remove files
                os.remove(file_path)