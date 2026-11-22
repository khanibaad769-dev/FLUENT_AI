import requests

# Local Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"


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

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTIONS
            },
            {
                "role": "user",
                "content": message.strip()
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 250
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            headers={
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=(5, 120)
        )

        response.raise_for_status()

        data = response.json()

        answer = data.get("message", {}).get("content", "")

        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("The AI returned an empty response.")

        return answer.strip()

    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "The AI took too long to respond. Please try again."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Local Ollama API error: HTTP {exc.response.status_code}. "
            "Check the model and Ollama server."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "Could not connect to local Ollama. "
            "Make sure Ollama is running."
        ) from exc