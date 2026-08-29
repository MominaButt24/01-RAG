# Graph RAG Implementation using Milvus metadata + Python-level 2-hop traversal

import os
import json
from dotenv import load_dotenv
from pymilvus import MilvusClient
from langchain_groq import ChatGroq

from src.config import VECTOR_DIMENSION, GROQ_MODEL_NAME, LLM_TEMPERATURE
from src.embedding.embedder import embed_query, embed_chunks

load_dotenv()

ZILLIZ_URI = os.getenv("ZILLIZ_URI")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN")

GRAPH_COLLECTION_NAME = "graph_triples_collection"

# Connect Milvus
_client = MilvusClient(uri=ZILLIZ_URI, token=ZILLIZ_TOKEN)
llm = ChatGroq(model=GROQ_MODEL_NAME, temperature=LLM_TEMPERATURE)


def reset_graph_collection():
    #it drops and recreates the graph triples collection in Milvus
    if _client.has_collection(collection_name=GRAPH_COLLECTION_NAME):
        _client.drop_collection(collection_name=GRAPH_COLLECTION_NAME)
    _client.create_collection(
        collection_name=GRAPH_COLLECTION_NAME,
        dimension=VECTOR_DIMENSION,
        metric_type="COSINE",
    )


def extract_triples_from_chunk(text: str) -> list[dict]:
    # 
    # Uses LLM to extract (Subject, Predicate, Object) triples from a text chunk.
    # 
    prompt = f"""
    You are an expert Knowledge Graph builder. 
    Extract key entity-relationship triples from the following text.
    Format your output strictly as a JSON list of objects with keys: "subject", "relation", "object".
    Do NOT include markdown block formatting, explanation, or extra text.

    Text:
    {text}

    JSON Output:
    """
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        # Clean up potential markdown formatting
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        triples = json.loads(content)
        return triples if isinstance(triples, list) else []
    except Exception as e:
        print(f"Error extracting triples: {e}")
        return []


def insert_graph_triples(chunks: list, filename: str) -> int:
    
    # Extracts triples from chunks, embeds the triple text representations, 
    # and saves them in Milvus with relational metadata (source_id, relation, target_id)

    if not _client.has_collection(collection_name=GRAPH_COLLECTION_NAME):
        reset_graph_collection()

    all_triples = []
    triple_texts = []

    for idx, chunk in enumerate(chunks):
        triples = extract_triples_from_chunk(chunk["text"])
        for t in triples:
            subj = str(t.get("subject", "")).strip().upper()
            rel = str(t.get("relation", "")).strip().replace(" ", "_").upper()
            obj = str(t.get("object", "")).strip().upper()

            if subj and rel and obj:
                # Text string used to generate vector embedding
                triple_str = f"{subj} {rel} {obj}"
                triple_texts.append(triple_str)
                all_triples.append({
                    "source_id": subj,
                    "relation": rel,
                    "target_id": obj,
                    "text": triple_str,
                    "filename": filename
                })

    if not triple_texts:
        return 0

    #now embeding the extracted triples
    embeddings = embed_chunks([{"text": txt} for txt in triple_texts])

    data_to_insert = [
        {
            "id": abs(hash(f"{filename}::{i}::{all_triples[i]['text']}")) % (10 ** 15),
            "vector": embeddings[i].tolist(),
            "text": all_triples[i]["text"],
            "source_id": all_triples[i]["source_id"],
            "relation": all_triples[i]["relation"],
            "target_id": all_triples[i]["target_id"],
            "filename": all_triples[i]["filename"],
        }
        for i in range(len(all_triples))
    ]

    result = _client.insert(collection_name=GRAPH_COLLECTION_NAME, data=data_to_insert)
    return result["insert_count"]


def retrieve_2hop_graph_context(query: str, top_k: int = 3) -> list[dict]:
    """
    Manual Python-level Multi-hop Graph Traversal using Milvus:
    1. Vector Similarity Search -> Find 1st-hop seed entities/triples.
    2. Metadata Filtering Query -> Fetch 2nd-hop triples attached to target_id.
    """
    _client.load_collection(collection_name=GRAPH_COLLECTION_NAME)

    # Hop 1: Find initial seed triples via vector search
    query_vector = embed_query(query)
    hop1_results = _client.search(
        collection_name=GRAPH_COLLECTION_NAME,
        data=[query_vector.tolist()],
        limit=top_k,
        output_fields=["text", "source_id", "relation", "target_id"],
    )

    retrieved_facts = []
    seen_triples = set()
    target_entities_for_hop2 = set()

    for hit in hop1_results[0]:
        entity = hit["entity"]
        triple_str = f"{entity['source_id']} --[{entity['relation']}]--> {entity['target_id']}"
        if triple_str not in seen_triples:
            seen_triples.add(triple_str)
            retrieved_facts.append({
                "hop": 1,
                "fact": triple_str,
                "score": hit["distance"]
            })
            target_entities_for_hop2.add(entity["target_id"])

    # Hop 2: Manual Metadata Lookup for connected entities
    if target_entities_for_hop2:
        # Construct Milvus filter expression for 2nd hop
        targets_str = ", ".join([f'"{t}"' for t in target_entities_for_hop2])
        filter_expr = f'source_id in [{targets_str}]'

        hop2_results = _client.query(
            collection_name=GRAPH_COLLECTION_NAME,
            filter=filter_expr,
            output_fields=["source_id", "relation", "target_id"],
            limit=10
        )

        for entity in hop2_results:
            triple_str = f"{entity['source_id']} --[{entity['relation']}]--> {entity['target_id']}"
            if triple_str not in seen_triples:
                seen_triples.add(triple_str)
                retrieved_facts.append({
                    "hop": 2,
                    "fact": triple_str,
                    "score": "Metadata-Filtered"
                })

    return retrieved_facts