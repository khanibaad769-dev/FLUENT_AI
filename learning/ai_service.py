import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL_NAME = "openai/gpt-oss-20b"

SYSTEM_INSTRUCTIONS = """
You are Fluent AI, an English-learning assistant.

Your responsibilities:
- Answer the user's actual question.
- Handle normal conversation naturally.
- Correct grammar when useful and explain mistakes simply.
- Help with vocabulary and conversational English.
- Give pronunciation tips when requested.
- Provide short, practical examples when useful.
- Keep answers concise and suitable for speaking aloud.
- Do not give unrelated lessons.
- Do not correct every sentence unless correction is useful or requested.
"""


def generate_ai_response(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Please provide a valid message.")

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTIONS,
            },
            {
                "role": "user",
                "content": message.strip(),
            },
        ],
        "temperature": 0.3,
        "max_completion_tokens": 300,
        "stream": False,
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=(10, 60),
        )

        response.raise_for_status()
        data = response.json()

        answer = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                "The AI returned an empty response."
            )

        return answer.strip()

    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "The AI took too long to respond. Please try again."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        status = (
            exc.response.status_code
            if exc.response is not None
            else "unknown"
        )

        raise RuntimeError(
            f"Groq API error ({status}). "
            "Check your API key, model and usage limits."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "Could not connect to the cloud AI service."
        ) from exc

    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "The AI returned an invalid response."
        ) from exc