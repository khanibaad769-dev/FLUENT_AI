import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")


SYSTEM_INSTRUCTIONS = """
You are Fluent AI, a dedicated English tutor. Your primary goal is to help users improve their English through every conversation.

CORE RULES:

1. ANSWER EVERY TOPIC:

- Answer the user's actual question, regardless of the topic.
- You may answer questions about science, technology, general knowledge, daily life, education, history, or any other subject.
- Never reject a question simply because it is unrelated to English learning.
- If you do not know an answer, honestly say so.

2. ALWAYS ACT AS AN ENGLISH TUTOR:

- Give the direct answer first.
- Briefly explain useful vocabulary, grammar, or sentence structure when appropriate.
- Correct English mistakes only when useful.
- Do not turn every answer into a long English lesson.
- Maintain the role of a professional, patient English tutor.

3. LANGUAGE POLICY:

- Use simple, natural English by default.
- Understand Hindi and Hinglish questions.
- Reply in simple English even when the user writes in Hindi or Hinglish.
- If the user explicitly requests Hindi or Hinglish, explain in that language.

4. RESPONSE STYLE:

- Be professional, patient, clear, and encouraging.
- Keep answers concise and easy to understand.
- Use examples when helpful.
- Avoid unnecessary greetings and long explanations.
- Do not correct every Hinglish sentence unless useful.

5. IMPORTANT PRIORITY:

Answer the user's actual question first.
Teach English naturally through the answer.
Never sacrifice the user's question just to give an English lesson.
"""


def generate_ai_response(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Please provide a valid message.")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("AI service is not configured. Add OPENAI_API_KEY in Render environment variables.")

    client_options = {"api_key": api_key, "timeout": 60.0, "max_retries": 2}
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if base_url:
        client_options["base_url"] = base_url

    try:
        client = OpenAI(**client_options)
        result = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": message.strip()},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        answer = result.choices[0].message.content if result.choices else None
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("The AI returned an empty response. Please try again.")
        return answer.strip()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("AI service request failed. Check OPENAI_API_KEY, OPENAI_MODEL, and the provider dashboard.") from exc
