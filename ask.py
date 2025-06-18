import json
import requests

def ask_question(question):
    try:
        with open("memory/log.jsonl", "r", encoding='utf-8') as f:
            logs = f.readlines()[-20:]  # Last 20 log entries
    except FileNotFoundError:
        return "❌ No memory log found."

    context = "".join(logs)
    prompt = f"Based on the following memory log, answer the question:\n\n{context}\n\nQuestion: {question}"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "tinyllama", "prompt": prompt},
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
