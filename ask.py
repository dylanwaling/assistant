import json
import requests

def ask_question(question):
    try:
        with open("memory/log.jsonl", "r") as f:
            logs = f.readlines()[-20:]
    except FileNotFoundError:
        return "❌ No memory log found."

    context = "".join(logs)
    prompt = f"Based on the memory log below, answer this question:\n\n{context}\n\nQuestion: {question}"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt},
            stream=True
        )
    except requests.exceptions.ConnectionError:
        return "❌ Could not connect to Ollama. Is it running?"

    answer = ""
    for chunk in response.iter_lines():
        if chunk:
            answer += chunk.decode("utf-8")

    return answer
