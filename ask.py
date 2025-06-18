import json
import requests
from config import OLLAMA_API, LLM_MODEL, MEMORY_DIR

def ask_question(question):
    log_path = f"{MEMORY_DIR}/log.jsonl"

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            logs = f.readlines()[-20:]  # Use last 20 entries for context
    except FileNotFoundError:
        return "❌ No memory log found."

    context = "".join(logs)
    prompt = f"Based on the following memory log, answer the question:\n\n{context}\n\nQuestion: {question}"

    try:
        response = requests.post(
            OLLAMA_API,
            json={"model": LLM_MODEL, "prompt": prompt},
            stream=True
        )
    except requests.exceptions.ConnectionError:
        return "❌ Could not connect to Ollama. Is it running?"

    answer = ""
    try:
        for chunk in response.iter_lines():
            if chunk:
                data = json.loads(chunk.decode("utf-8"))
                answer += data.get("response", "")
    except Exception as e:
        return f"⚠️ Error parsing LLM response: {e}"

    return answer.strip() if answer.strip() else "⚠️ No answer generated."
