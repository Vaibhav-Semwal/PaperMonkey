"""
Talks to the locally-running Qwen model via Ollama's OpenAI-compatible
chat completions endpoint.
"""
import os
import json
import httpx

QWEN_API_BASE_URL = os.environ.get("QWEN_API_BASE_URL", "http://qwen:11434/v1")
QWEN_MODEL_NAME = os.environ.get("QWEN_MODEL_NAME", "qwen2.5:0.5b")


async def generate_section_questions(topic_context: str, num_questions: int, marks_per_question: int):
    prompt = (
        "You are creating exam questions from the reference material below.\n\n"
        f"Reference material:\n\"\"\"\n{topic_context}\n\"\"\"\n\n"
        f"Write exactly {num_questions} question-and-answer pairs based on the "
        "reference material above. Each question is worth "
        f"{marks_per_question} marks (make questions harder/more detailed for "
        "higher marks). Respond with ONLY a JSON array, no other text, in this "
        'exact format:\n[{"question": "...", "answer": "..."}, ...]'
    )

    payload = {
        "model": QWEN_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{QWEN_API_BASE_URL}/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

    raw_content = data["choices"][0]["message"]["content"].strip()
    return _parse_questions_json(raw_content, num_questions)


def _parse_questions_json(raw_content: str, expected_count: int):
    cleaned = raw_content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Qwen did not return valid JSON: {e}\nRaw output: {raw_content[:500]}")

    if not isinstance(parsed, list):
        raise ValueError("Qwen response was not a JSON array")

    questions = []
    for item in parsed[:expected_count]:
        if isinstance(item, dict) and "question" in item and "answer" in item:
            questions.append({"question": str(item["question"]), "answer": str(item["answer"])})
    return questions