import hashlib
import chromadb


client = chromadb.PersistentClient(path="chroma_storage")

collection = client.get_or_create_collection(
    name="medical_rag"
)


def generate_chunk_id(source_file: str, page_number: int, chunk: str) -> str:
    unique_text = f"{source_file}_{page_number}_{chunk}"
    return hashlib.md5(unique_text.encode("utf-8")).hexdigest()


def store_embeddings(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict]
):
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

    print(f"Stored {len(new_chunks)} new embeddings.")