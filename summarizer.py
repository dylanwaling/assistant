import requests
import json
from memory_engine import log_event
from config import OLLAMA_API, LLM_MODEL

def summarize_file(path):
    print(f"📄 Attempting to summarize: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except PermissionError:
        print(f"❌ Cannot access file (locked): {path}")
        return

    if not content.strip():
        print(f"⚠️ Skipping empty file: {path}")
        return

    prompt = f"Summarize this:\n\n{content}"

    try:
        response = requests.post(
            OLLAMA_API,
            json={"model": LLM_MODEL, "prompt": prompt},
            stream=True
        )
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running. Start it with: ollama run <model>")
        return

    summary = ""
    try:
        for chunk in response.iter_lines():
            if chunk:
                data = json.loads(chunk.decode("utf-8"))
                if "response" in data:
                    summary += data["response"]
    except Exception as e:
        print(f"⚠️ Failed to parse response: {e}")
        return

    summary = summary.strip()
    if summary:
        log_event(summary, path)
        print(f"✅ Summary complete: {summary[:80]}...")
    else:
        print("⚠️ LLM returned empty summary.")
