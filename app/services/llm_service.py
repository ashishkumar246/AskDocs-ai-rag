import ollama


def _ask_ollama(prompt: str) -> str:
    response = ollama.chat(
        model="phi3",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


def generate_response(query: str, context_chunks: list[dict]) -> str:
    context = "\n\n".join(
        [
            f"""Context chunk {index}
Source file: {chunk["source_file"]}
Page: {chunk["page_number"]}
Chunk index: {chunk["chunk_index"]}
Text:
{chunk["text"]}"""
            for index, chunk in enumerate(context_chunks, start=1)
        ]
    )

    prompt = f"""
You are a document-grounded assistant.

Your job:
Answer the user's question using ONLY the provided document context.

Rules:
1. If the context contains the answer, answer clearly and directly.
2. If the context does not contain the answer, say exactly:
"I could not find that information in the document."
3. Do not say "I could not find" if relevant context exists.
4. Keep answers concise and clean.
5. Do not add extra explanations or outside knowledge.
6. Do not mention sources, references, citations, or links.
7. Ignore broken PDF formatting, random symbols, and reference sections.
8. Preserve names, titles, organizations, dates, and labels exactly as written in the context.
9. Do not combine an organization from one entry with dates, role names, or details from another entry.
10. If the question asks about internships, use only entries or sections that are labeled as internship, internships, intern, or trainee.
11. If multiple matching entries exist, list each one separately.

Document context:
{context}

User question:
{query}

Final answer:
"""

    return _ask_ollama(prompt)
