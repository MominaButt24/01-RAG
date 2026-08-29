# this is the only file that talks to every stage.
# Nothing outside this file (like main.py) should need to know HOW
# ingestion/embedding/storage/generation work internally
#-simple rag pipeline

import os

from src.ingestion.file_processor import process_file
from src.embedding.embedder import embed_chunks, embed_query
from src.vectorstore import milvus_store
from src.config import UPLOAD_DIR
import sentry_sdk

import sentry_sdk

def ingest_file(file_path: str) -> int:
    """
    Full ingestion pipeline for ONE file:
    read file -> chunk it -> embed chunks -> store in Milvus, tagged with
    the file's name so it can later be listed or deleted individually.
    Returns how many chunks were stored.
    """
    filename = os.path.basename(file_path)

    # --- Stage 1: Parse & chunk ---
    with sentry_sdk.start_span(op="rag.parse", description="Parse & chunk file") as span:
        chunks = process_file(file_path)
        span.set_data("num_chunks", len(chunks))

        if not chunks:
            sentry_sdk.set_context("ingestion", {"filename": filename, "file_path": file_path})
            sentry_sdk.capture_message(f"No chunks produced from {filename} — ingestion yielded nothing", level="warning")
            return 0

    # --- Stage 2: Embed chunks ---
    with sentry_sdk.start_span(op="rag.embed_chunks", description="Embed document chunks") as span:
        embeddings = embed_chunks(chunks)
        span.set_data("num_embeddings", len(embeddings))

    # --- Stage 3: Store in Milvus ---
    with sentry_sdk.start_span(op="rag.store", description="Milvus insert"):
        try:
            inserted_count = milvus_store.insert_chunks(chunks, embeddings, filename)
        except Exception as e:
            sentry_sdk.set_context("ingestion", {
                "filename": filename,
                "num_chunks_embedded": len(chunks),
                "embedding_dims": len(embeddings[0]) if embeddings else None,
            })
            sentry_sdk.capture_exception(e)
            raise

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

    #embedding query
    with sentry_sdk.start_span(op="rag.embed", description="Embed query"):
        query_vector = embed_query(query)

    # milvus reterival
    with sentry_sdk.start_span(op="rag.retrieve", description="Milvus retrieval") as span:
        retrieved_chunks = milvus_store.search(query_vector, limit=top_k)
        span.set_data("num_chunks_retrieved", len(retrieved_chunks))

        if not retrieved_chunks:
            sentry_sdk.set_context("retrieval", {"query": query, "top_k": top_k})
            sentry_sdk.capture_message("Empty retrieval: no chunks found for query", level="warning")

        #groq generation 
    with sentry_sdk.start_span(op="rag.generate", description="Groq generation"):
        try:
            answer = generate_answer(query, retrieved_chunks)
        except Exception as e:
            sentry_sdk.set_context("generation", {
                "query": query,
                "num_context_chunks": len(retrieved_chunks),
            })
            sentry_sdk.capture_exception(e)
            raise


    # query_vector = embed_query(query)
    # retrieved_chunks = milvus_store.search(query_vector, limit=top_k)
    # answer = generate_answer(query, retrieved_chunks)

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