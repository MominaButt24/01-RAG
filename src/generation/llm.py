"""
Generation stage: takes retrieved chunks + the user's question, and asks
the LLM to answer using ONLY that context (grounded answer, not made up).
"""

from dotenv import load_dotenv
from groq import Groq
from src.config import GROQ_MODEL_NAME, LLM_TEMPERATURE, SYSTEM_INSTRUCTION

load_dotenv()
_client = Groq()


def build_context_block(retrieved_chunks: list) -> str:
    
    # Turns retrieved chunk dicts into one formatted text block the LLM
    # can read, with source + similarity score visible per chunk so later
    # can trace an answer back to exactly where it came from.
    
    parts = []
    for ch in retrieved_chunks:
        parts.append(f"[{ch['source']}] (similarity: {ch['score']}):\n{ch['text']}")
    return "\n-----\n".join(parts)


def generate_answer(query: str, retrieved_chunks: list) -> str:
    context_block = build_context_block(retrieved_chunks)

    user_prompt = f"""--- RETRIEVED CONTEXT ---
{context_block}

--- USER QUESTION ---
{query}"""

    chat_completion = _client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_prompt},
        ],
        model=GROQ_MODEL_NAME,
        temperature=LLM_TEMPERATURE,
    )
    return chat_completion.choices[0].message.content
