import ollama


def generate_response(query: str, context_chunks: list[dict]) -> str:
    context = "\n\n".join([chunk["text"] for chunk in context_chunks])

    prompt = f"""
You are an exper Nutrition AI assistant.

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

Document context:
{context}

User question:
{query}

Final answer:
"""

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