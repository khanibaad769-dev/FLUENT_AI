import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTIONS = """
You are Fluent AI, a dedicated English tutor and general learning assistant.
Answer the user's actual question first. Understand Hindi and Hinglish, and
reply in the language the user uses unless they request another language.
Use simple, natural language. Correct English mistakes only when useful.
Keep answers clear, practical, and concise. For interview preparation, give
specific, realistic answers and explain how to improve them.
"""


def generate_ai_response(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Please provide a valid message.")

    # Render already has GROQ_API_KEY. Support it directly instead of requiring
    # a second secret with a different name.
    api_key = (
        os.getenv("GROQ_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
    )
    if not api_key:
        raise RuntimeError("AI is not configured. Add GROQ_API_KEY in Render Environment.")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1").strip()
    model = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b").strip()

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=45.0,
            max_retries=1,
        )
        result = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": message.strip()},
            ],
            temperature=0.3,
            max_tokens=600,
        )
        answer = result.choices[0].message.content if result.choices else None
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("The AI provider returned an empty response.")
        return answer.strip()
    except Exception as exc:
        logger.exception("Fluent AI provider request failed")
        raise RuntimeError(f"AI provider error: {exc}") from exc
