from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from typing import Annotated
import uuid
import re
from pydantic import BaseModel


from app.rag.pdf_loader import load_pdf_pages
from app.rag.chunker import recursive_chunk_text
from app.rag.embedder import create_embeddings
from app.db.chroma_db import collection_exists, delete_collection, store_embeddings
from app.rag.retriever import (
    get_collection_count,
    retrieve_relevant_chunks
)
from app.services.llm_service import generate_response
from app.db.chroma_db import DEFAULT_COLLECTION_NAME


router = APIRouter()
active_upload_collection_name = None
active_upload_files = []


class QuestionRequest(BaseModel):
    question: str
    collection_name: str = DEFAULT_COLLECTION_NAME


class ClearUploadRequest(BaseModel):
    collection_name: str


def filter_chunks_for_question(question: str, chunks: list[dict]) -> list[dict]:
    normalized_question = question.lower()
    internship_pattern = r"\b(intern|internship|internships|trainee)\b"

    if re.search(internship_pattern, normalized_question):
        internship_chunks = [
            chunk for chunk in chunks
            if re.search(internship_pattern, chunk["text"].lower())
        ]

        if internship_chunks:
            return internship_chunks

    return chunks


@router.get("/active-collection")
def get_active_collection():
    return {
        "collection_name": active_upload_collection_name or DEFAULT_COLLECTION_NAME,
        "using_uploaded_pdf": active_upload_collection_name is not None,
        "uploaded_files": active_upload_files
    }


@router.post("/ask")
def ask_question(request: QuestionRequest):
    global active_upload_collection_name

    collection_name = request.collection_name

    if collection_name == DEFAULT_COLLECTION_NAME and active_upload_collection_name:
        collection_name = active_upload_collection_name

    is_user_upload = collection_name.startswith("user_upload_")

    if is_user_upload and collection_name != active_upload_collection_name:
        if not collection_exists(collection_name) or get_collection_count(collection_name) == 0:
            return {
                "question": request.question,
                "collection_name": DEFAULT_COLLECTION_NAME,
                "answer": "The uploaded PDF is no longer active. Please upload it again before asking questions from it.",
                "sources_used": []
            }

        active_upload_collection_name = collection_name

    if is_user_upload:
        chunks = retrieve_relevant_chunks(
            query=request.question,
            collection_name=collection_name,
            top_k=5,
            max_distance=None
        )
        chunks = filter_chunks_for_question(request.question, chunks)
    else:
        chunks = retrieve_relevant_chunks(
            query=request.question,
            collection_name=collection_name,
            top_k=3,
            max_distance=1.6
        )

    if not chunks:
        answer = "I could not find that information in the document."
        return {
            "question": request.question,
            "collection_name": collection_name,
            "answer": answer,
            "sources_used": []
        }

    answer = generate_response(request.question, chunks)

    sources = []

    for chunk in chunks:
        sources.append({
            "source_file": chunk["source_file"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "distance": round(chunk["distance"], 3)
        })

    return {
        "question": request.question,
        "collection_name": collection_name,
        "answer": answer,
        "sources_used": sources
    }

@router.post("/upload-pdfs")
async def upload_pdfs(files: Annotated[list[UploadFile], File(...)]):
    global active_upload_collection_name, active_upload_files

    if active_upload_collection_name:
        delete_collection(active_upload_collection_name)
        active_upload_collection_name = None
        active_upload_files = []

    collection_name = f"user_upload_{uuid.uuid4().hex[:8]}"

    upload_folder = Path("uploaded_pdfs")
    upload_folder.mkdir(exist_ok=True)

    uploaded_files = []
    total_chunks = 0

    for file in files:
        safe_filename = Path(file.filename).name

        if not safe_filename.lower().endswith(".pdf"):
            continue

        file_path = upload_folder / safe_filename

        content = await file.read()

        try:
            with open(file_path, "wb") as f:
                f.write(content)

            pages = load_pdf_pages(str(file_path))

            all_chunks = []
            all_metadatas = []

            for page in pages:
                page_number = page["page_number"]
                page_text = page["text"]

                chunks = recursive_chunk_text(page_text)

                for chunk_index, chunk in enumerate(chunks):
                    all_chunks.append(chunk)

                    all_metadatas.append({
                        "source_file": safe_filename,
                        "page_number": page_number,
                        "chunk_index": chunk_index
                    })

            if not all_chunks:
                continue

            embeddings = create_embeddings(all_chunks)

            store_embeddings(
                chunks=all_chunks,
                embeddings=embeddings,
                metadatas=all_metadatas,
                collection_name=collection_name
            )

            uploaded_files.append(safe_filename)
            total_chunks += len(all_chunks)
        finally:
            if file_path.exists():
                file_path.unlink()

    if uploaded_files:
        active_upload_collection_name = collection_name
        active_upload_files = uploaded_files
    else:
        delete_collection(collection_name)
        raise HTTPException(
            status_code=400,
            detail="No readable PDF text was found. Please upload a text-based PDF, not a scanned image PDF."
        )

    return {
        "message": "PDFs uploaded and ingested successfully.",
        "collection_name": collection_name,
        "uploaded_files": uploaded_files,
        "chunk_count": total_chunks
    }


@router.post("/clear-upload")
def clear_upload(request: ClearUploadRequest):
    global active_upload_collection_name, active_upload_files

    delete_collection(request.collection_name)
    if active_upload_collection_name == request.collection_name:
        active_upload_collection_name = None
        active_upload_files = []

    return {
        "message": "Uploaded PDF collection cleared.",
        "collection_name": DEFAULT_COLLECTION_NAME
    }
