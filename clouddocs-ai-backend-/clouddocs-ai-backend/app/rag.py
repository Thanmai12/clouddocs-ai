from groq import Groq

from app.config import settings
from app.vectorstore import query_chunks

_client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are a document Q&A assistant. Answer the user's question using ONLY the
provided source passages. If the passages do not contain enough information to answer,
say clearly that the document does not mention it — do not guess or use outside knowledge.

Structure every answer like this:
1. Start with ONE bolded sentence that directly answers the question (the headline).
2. Follow with a blank line, then supporting details as a bulleted list — one fact per bullet.
3. Bold any specific numbers, dates, durations, or named terms inside the bullets.
4. Keep each bullet to one short sentence. Never write a dense paragraph.
5. If the question has no clear answer in the passages, just say so in one bolded
   sentence — skip the bullets entirely.

Example shape:
**Refunds are accepted within 30 days of purchase.**

- Item must be **unused** and in its **original packaging**
- Refunds are processed within **5–7 business days** after the return is received
"""


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
