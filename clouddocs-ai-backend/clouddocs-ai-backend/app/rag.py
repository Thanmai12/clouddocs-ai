from groq import Groq

from app.config import settings
from app.vectorstore import query_chunks

_client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are a document Q&A assistant. Answer the user's question using ONLY the
provided source passages. If the passages do not contain enough information to answer,
say clearly that the document does not mention it — do not guess or use outside knowledge.
Keep answers concise and directly grounded in the passages."""


def answer_question(document_id: str, question: str) -> dict:
    passages = query_chunks(document_id, question, top_k=4)

    if not passages:
        return {
            "answer": "This document hasn't been indexed yet, or no content could be retrieved.",
            "sources": [],
            "grounded": False,
        }

    context = "\n\n".join(
        f"[Passage {i+1}]\n{p['text']}" for i, p in enumerate(passages)
    )

    user_prompt = f"""Source passages:
{context}

Question: {question}

Answer using only the passages above. If they don't contain the answer, say so plainly."""

    response = _client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    answer_text = response.choices[0].message.content
    grounded = "does not mention" not in answer_text.lower() and "don't know" not in answer_text.lower()

    return {
        "answer": answer_text,
        "sources": passages,
        "grounded": grounded,
    }
