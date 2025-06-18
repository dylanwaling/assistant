import requests
from memory_engine import log_event

def summarize_file(path):
    try:
        with open(path, 'r') as f:
            content = f.read()
    except PermissionError:
        print(f"❌ Skipped locked file: {path}")
        return

    if not content.strip():
        print(f"⚠️ Skipping empty file: {path}")
        return

    print(f"📄 Summarizing file: {path}")
    prompt = f"Summarize the following:\n\n{content}"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt},
            stream=True
        )
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Ollama. Is it running?")
        return

    summary = ""
    for chunk in response.iter_lines():
        if chunk:
            summary += chunk.decode("utf-8")

    log_event(summary, path)
    print("✅ Summary logged.")
