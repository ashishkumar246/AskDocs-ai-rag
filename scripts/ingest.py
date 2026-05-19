from pathlib import Path

from app.rag.pdf_loader import load_pdf_pages
from app.rag.chunker import recursive_chunk_text
from app.rag.embedder import create_embeddings
from app.db.chroma_db import store_embeddings


DATA_FOLDER = "data"


def ingest_pdf(pdf_path: Path):
    print(f"\nProcessing: {pdf_path.name}")

    pages = load_pdf_pages(str(pdf_path))

    all_chunks = []
    all_metadatas = []

    for page in pages:
        page_number = page["page_number"]
        page_text = page["text"]

        chunks = recursive_chunk_text(page_text)

        for chunk_index, chunk in enumerate(chunks):
            all_chunks.append(chunk)

            all_metadatas.append({
                "source_file": pdf_path.name,
                "page_number": page_number,
                "chunk_index": chunk_index
            })

    embeddings = create_embeddings(all_chunks)

    store_embeddings(
        chunks=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas
    )


def main():
    pdf_files = Path(DATA_FOLDER).glob("*.pdf")

    for pdf_file in pdf_files:
        ingest_pdf(pdf_file)


if __name__ == "__main__":
    main()