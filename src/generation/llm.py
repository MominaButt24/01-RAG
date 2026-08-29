# src/generation/llm.py
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
    parts = []
    for ch in retrieved_chunks:
        # Get source metadata (or fallback)
        source = ch.get("source", ch.get("hop", "Unknown Source"))
        
        # Safe format for similarity score or rank
        score = ch.get("score", "N/A")
        score_str = f"{score:.4f}" if isinstance(score, float) else str(score)
        
        # Retrieve text or fact
        text = ch.get("text", ch.get("fact", str(ch)))
        
        parts.append(f"[{source}] (score/info: {score_str}):\n{text}")
        
    return "\n\n".join(parts)


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