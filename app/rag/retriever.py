from app.rag.embedder import create_embeddings
from app.db.chroma_db import get_collection, DEFAULT_COLLECTION_NAME
from chromadb.errors import NotFoundError


def retrieve_all_chunks(collection_name: str):
    collection = get_collection(collection_name)

    results = collection.get(
        include=["documents", "metadatas"]
    )

    chunks = []

    for document, metadata in zip(results["documents"], results["metadatas"]):
        metadata = metadata or {}

        chunks.append({
            "text": document,
            "source_file": metadata.get("source_file", "unknown"),
            "page_number": metadata.get("page_number", 0),
            "chunk_index": metadata.get("chunk_index", 0),
            "distance": 0
        })

    return sorted(
        chunks,
        key=lambda chunk: (
            chunk["source_file"],
            chunk["page_number"],
            chunk["chunk_index"]
        )
    )


def get_collection_count(collection_name: str) -> int:
    collection = get_collection(collection_name)
    return collection.count()


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 3,
    max_distance: float | None = 1.6,
    collection_name: str = DEFAULT_COLLECTION_NAME
):
    collection = get_collection(collection_name)

    try:
        collection_count = collection.count()
    except NotFoundError:
        return []

    if collection_count == 0:
        return []

    query_embedding = create_embeddings([query])[0]

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection_count)
        )
    except NotFoundError:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved_chunks = []

    for document, metadata, distance in zip(documents, metadatas, distances):
        metadata = metadata or {}

        if max_distance is None or distance <= max_distance:
            retrieved_chunks.append({
                "text": document,
                "source_file": metadata.get("source_file", "unknown"),
                "page_number": metadata.get("page_number", "unknown"),
                "chunk_index": metadata.get("chunk_index", "unknown"),
                "distance": distance
            })

    return retrieved_chunks
