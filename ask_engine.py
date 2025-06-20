import json
import requests
import sys
import time
from config import LLM_MODEL, OLLAMA_API
from memory_index import search_memory

def ask_question(question):
    t0 = time.time()
    print("[🔍] Searching memory...", flush=True)
    matches = search_memory(
        question,
        top_k=10,
        where={"type": "deletion"}
    )
    t1 = time.time()

    print("\n[🗂️] Retrieved memory entries for LLM context:", flush=True)
    for i, (summary, meta) in enumerate(matches, 1):
        print(f"{i}. [{meta.get('timestamp', meta.get('date', 'unknown'))}] ({meta.get('source', 'unknown')})\n   {summary}", flush=True)

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

    print(f"[🤖] Querying LLM ({LLM_MODEL})...", flush=True)
    try:
        response = requests.post(
            OLLAMA_API,
            json={"model": LLM_MODEL, "prompt": prompt},
            stream=True,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        return f"❌ Could not connect to Ollama: {e}"

    print("[💬] LLM response:", flush=True)
    sys.stdout.flush()
    chunks = []
    for line in response.iter_lines():
        if not line:
            continue
        try:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                chunk = data["response"]
                print(chunk, end="", flush=True)  # Live update
                chunks.append(chunk)
        except Exception as e:
            print(f"\n⚠️ Skipping invalid chunk: {e}", flush=True)

    t2 = time.time()
    print(f"\n[⏱️] Memory search: {t1-t0:.2f}s | LLM: {t2-t1:.2f}s | Total: {t2-t0:.2f}s", flush=True)
    answer = "".join(chunks).strip()
    return answer if answer else "⚠️ No answer generated."