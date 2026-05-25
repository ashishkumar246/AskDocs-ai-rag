import hashlib
import chromadb


client = chromadb.PersistentClient(path="chroma_storage")


DEFAULT_COLLECTION_NAME = "medical_rag"


def get_collection(collection_name: str = DEFAULT_COLLECTION_NAME):
    return client.get_or_create_collection(
        name=collection_name
    )


def collection_exists(collection_name: str) -> bool:
    try:
        client.get_collection(name=collection_name)
        return True
    except Exception:
        return False


def delete_collection(collection_name: str):
    if collection_name == DEFAULT_COLLECTION_NAME:
        raise ValueError("Default collection cannot be deleted.")

    try:
        client.delete_collection(name=collection_name)
    except Exception as exc:
        print(f"Could not delete collection {collection_name}: {exc}")


def delete_user_upload_collections():
    for collection in client.list_collections():
        if collection.name.startswith("user_upload_"):
            delete_collection(collection.name)


def generate_chunk_id(source_file: str, page_number: int, chunk: str) -> str:
    unique_text = f"{source_file}_{page_number}_{chunk}"
    return hashlib.md5(unique_text.encode("utf-8")).hexdigest()


def store_embeddings(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    collection_name: str = DEFAULT_COLLECTION_NAME
):
    collection = get_collection(collection_name)

    ids = [
        generate_chunk_id(
            metadata["source_file"],
            metadata["page_number"],
            chunk
        )
        for chunk, metadata in zip(chunks, metadatas)
    ]

    existing = collection.get(ids=ids)
    existing_ids = set(existing["ids"])

    new_chunks = []
    new_embeddings = []
    new_metadatas = []
    new_ids = []

    for chunk, embedding, metadata, chunk_id in zip(chunks, embeddings, metadatas, ids):
        if chunk_id not in existing_ids:
            new_chunks.append(chunk)
            new_embeddings.append(embedding)
            new_metadatas.append(metadata)
            new_ids.append(chunk_id)

    if not new_chunks:
        print("No new chunks to store.")
        return

    collection.add(
        ids=new_ids,
        documents=new_chunks,
        embeddings=new_embeddings,
        metadatas=new_metadatas
    )

    print(f"Stored {len(new_chunks)} new embeddings in collection: {collection_name}")
