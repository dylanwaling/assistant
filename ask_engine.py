import json
import requests
from config import LLM_MODEL, OLLAMA_API
from memory_index import search_memory

def ask_question(question):
    matches = search_memory(question, top_k=10)

    if not matches:
        return "❌ No relevant memory entries found."

    context = "\n\n".join(
    f"[{meta.get('timestamp', meta.get('date', 'unknown'))}] ({meta.get('source', 'unknown')})\n{summary}" 
    for summary, meta in matches
)


    prompt = f"""Based on the following memory log entries, answer the question:

{context}

Question: {question}
"""

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
