import json
import requests
from config import LLM_MODEL, OLLAMA_API

def ask_question(question):
    try:
        with open("memory/log.jsonl", "r", encoding='utf-8') as f:
            logs = f.readlines()[-20:]  # Last 20 memory entries
    except FileNotFoundError:
        return "❌ No memory log found."

    context = "".join(logs)
    prompt = f"Based on the following memory log, answer the question:\n\n{context}\n\nQuestion: {question}"

    try:
        response = requests.post(
            OLLAMA_API,
            json={"model": LLM_MODEL, "prompt": prompt},
            stream=True,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        return f"❌ Could not connect to Ollama: {e}"

    chunks = []
    for line in response.iter_lines():
        if not line:
            continue
        try:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                chunks.append(data["response"])
        except Exception as e:
            print(f"⚠️ Skipping invalid chunk: {e}")

    answer = "".join(chunks).strip()
    return answer if answer else "⚠️ No answer generated."
