import hashlib
import chromadb


client = chromadb.PersistentClient(path="chroma_storage")

collection = client.get_or_create_collection(
    name="medical_rag"
)


def generate_chunk_id(chunk: str) -> str:
    return hashlib.md5(chunk.encode("utf-8")).hexdigest()


def store_embeddings(
    chunks: list[str],
    embeddings: list[list[float]]
):
    ids = [generate_chunk_id(chunk) for chunk in chunks]

    existing = collection.get(ids=ids)
    existing_ids = set(existing["ids"])

    new_chunks = []
    new_embeddings = []
    new_ids = []

    for chunk, embedding, chunk_id in zip(chunks, embeddings, ids):
        if chunk_id not in existing_ids:
            new_chunks.append(chunk)
            new_embeddings.append(embedding)
            new_ids.append(chunk_id)

    if not new_chunks:
        print("No new chunks to store.")
        return

    collection.add(
        ids=new_ids,
        documents=new_chunks,
        embeddings=new_embeddings
    )

    print(f"Stored {len(new_chunks)} new embeddings.")