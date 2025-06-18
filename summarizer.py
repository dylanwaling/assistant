import requests
from memory_engine import log_event

def summarize_file(path):
    with open(path, 'r') as f:
        content = f.read()

    prompt = f"Summarize the following file:\n\n{content}"
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3", "prompt": prompt},
        stream=True
    )

    summary = ""
    for chunk in response.iter_lines():
        if chunk:
            summary += chunk.decode("utf-8")

    log_event(summary, path)
    return summary
