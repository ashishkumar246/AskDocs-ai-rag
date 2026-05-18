from app.rag.embedder import create_embeddings
from app.db.chroma_db import collection


def retrieve_relevant_chunks(query: str, top_k: int = 3, max_distance: float = 1.6):
    query_embedding = create_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    documents = results["documents"][0]
    distances = results["distances"][0]

    filtered_chunks = []

    for doc, distance in zip(documents, distances):
        if distance <= max_distance:
            filtered_chunks.append(doc)

    return filtered_chunks