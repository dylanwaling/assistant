import json
import requests

def ask_question(question):
    with open("memory/log.jsonl", "r") as f:
        logs = f.readlines()[-20:]

    context = "".join(logs)
    prompt = f"Here is a memory log:\n{context}\n\nAnswer this question:\n{question}"

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3", "prompt": prompt},
        stream=True
    )

    answer = ""
    for chunk in response.iter_lines():
        if chunk:
            answer += chunk.decode("utf-8")

    return answer
