from pathlib import Path
from typing import List
import chromadb
from chromadb.utils import embedding_functions

from src.schemas import RAGAgentResult, RetrievedChunk, RAGTaskSpec

CHROMA_PATH = Path(__file__).resolve().parent.parent.parent / "chroma_db"
COLLECTION_NAME = "bistro_faq"

def get_faq_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)

def retrieve_faq_context(task_spec: RAGTaskSpec) -> RAGAgentResult:
    """
    Queries ChromaDB with the task specification and returns typed chunks.
    """
    collection = get_faq_collection()
    
    results = collection.query(
        query_texts=[task_spec.query],
        n_results=task_spec.top_k
    )
    
    retrieved_chunks: List[RetrievedChunk] = []
    
    # Chroma returns lists of lists for queries
    if results and results["documents"] and results["ids"]:
        docs = results["documents"][0]
        ids = results["ids"][0]
        # Distances can be converted to an approximate similarity score (1 - distance)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
        
        for doc_id, doc_text, dist in zip(ids, docs, distances):
            # Chroma default L2 distance: lower is closer; score normalized for readability
            score = round(max(0.0, 1.0 - (dist / 2.0)), 3)
            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=doc_id,
                    content=doc_text,
                    relevance_score=score
                )
            )
            
    return RAGAgentResult(
        query=task_spec.query,
        retrieved_chunks=retrieved_chunks
    )