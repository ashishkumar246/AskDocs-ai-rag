from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.retriever import retrieve_relevant_chunks
from app.services.llm_service import generate_response


router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_question(request: QuestionRequest):
    chunks = retrieve_relevant_chunks(request.question)

    if not chunks:
        answer = "I could not find that information in the document." #threshhold lagana ha 
        return {
            "question": request.question,
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
        "answer": answer,
        "sources_used": sources
    }