# src/vectorstore/neo4j_store.py
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class Neo4jGraphStore:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def reset_graph(self):
        """Clears the entire Neo4j database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def insert_triples(self, triples: list, source_file: str):
        """
        Inserts extracted triples into Neo4j using MERGE.
        Expected triple dict: {'subject': '...', 'predicate': '...', 'object': '...'}
        """
        cypher_standard = """
        UNWIND $triples AS t
        MERGE (s:Entity {name: toUpper(t.subject)})
        MERGE (o:Entity {name: toUpper(t.object)})
        MERGE (s)-[r:RELATED {type: toUpper(t.predicate), file: $source_file}]->(o)
        """
        with self.driver.session() as session:
            session.run(cypher_standard, triples=triples, source_file=source_file)
        return len(triples)

    def search_2hop_subgraph(self, entity_names: list) -> list:
        """
        Traverses up to 2 hops out from extracted entities and returns graph facts.
        """
        cypher = """
        MATCH (s:Entity) WHERE s.name IN $entity_names
        MATCH path = (s)-[r:RELATED*1..2]-(target:Entity)
        UNWIND relationships(path) AS rel
        RETURN DISTINCT 
            startNode(rel).name AS subject, 
            rel.type AS predicate, 
            endNode(rel).name AS object,
            length(path) AS hop
        LIMIT 25
        """
        facts = []
        with self.driver.session() as session:
            result = session.run(cypher, entity_names=[e.upper() for e in entity_names])
            for record in result:
                facts.append({
                    "hop": record["hop"],
                    "fact": f"{record['subject']} --[{record['predicate']}]--> {record['object']}"
                })
        return facts


neo4j_store = Neo4jGraphStore()