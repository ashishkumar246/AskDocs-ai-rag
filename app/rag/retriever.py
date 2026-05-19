from app.rag.embedder import create_embeddings
from app.db.chroma_db import collection


def retrieve_relevant_chunks(query: str, top_k: int = 3, max_distance: float = 1.6):
    query_embedding = create_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved_chunks = []

    for document, metadata, distance in zip(documents, metadatas, distances):

        if distance <= max_distance:

            retrieved_chunks.append({
                "text": document,
                "source_file": metadata["source_file"],
                "page_number": metadata["page_number"],
                "chunk_index": metadata["chunk_index"],
                "distance": distance
            })

    return retrieved_chunks