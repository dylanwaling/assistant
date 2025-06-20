# core.py
# Core logic for assistant: memory, embedding, summarization, file watching, and LLM interaction.

import os
import sys
import json
import time
from datetime import datetime, timedelta

import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === Embedding ===
# Provides vector embeddings for text using sentence-transformers.
try:
    from sentence_transformers import SentenceTransformer
    _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    def embed(text: str) -> list[float]:
        """Return a vector embedding for the given text."""
        return _embed_model.encode(text).tolist()
except ImportError:
    def embed(text: str) -> list[float]:
        raise ImportError("sentence-transformers not installed")

# === ChromaDB Memory Index ===
# Handles persistent vector storage and retrieval.
try:
    import chromadb
    _client = chromadb.PersistentClient(path="chromadb_store")
    collection = _client.get_or_create_collection("memory")
except ImportError:
    collection = None

from config import (
    WORKSPACE_DIR, MEMORY_DIR, OUTPUT_DIR,
    LLM_MODEL, OLLAMA_API, MAX_TOKENS, IGNORED_EXTENSIONS
)

def add_memory(id: str, text: str, metadata: dict = {}):
    """Add a memory entry to the ChromaDB vector store."""
    if collection is None:
        print("ChromaDB not available.")
        return
    embedding = embed(text)
    collection.add(
        documents=[text],
        ids=[id],
        embeddings=[embedding],
        metadatas=[metadata]
    )

def search_memory(query: str, top_k=5, where: dict = None):
    """Search memory entries using a vector query and optional metadata filter."""
    if collection is None:
        print("ChromaDB not available.")
        return []
    query_vector = embed(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where=where or {}
    )
    return list(zip(results["documents"][0], results["metadatas"][0]))

def list_all_memories():
    """Print all memory entries in the database."""
    if collection is None:
        print("ChromaDB not available.")
        return
    results = collection.get()
    if not results["documents"]:
        print("🧠 No memory entries found in the database.")
        return
    for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
        print(f"\n#{i+1}")
        print(f"[{meta.get('timestamp', 'unknown')}] ({meta.get('source', 'unknown')})")
        print(doc)

# === Memory Logging ===
STATE_FILE = os.path.join(MEMORY_DIR, "last_seen.json")
LOG_FILE = os.path.join(MEMORY_DIR, "log.jsonl")

def log_event(summary, source_path, event_type="summary"):
    """Log a memory event (summary, deletion, etc.) to disk."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source_path,
        "type": event_type,
        "summary": summary
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # Optionally call cleanup_chromadb() here if needed.

def load_file_state():
    """Load the last seen file modification times from disk."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_file_state(state):
    """Save the last seen file modification times to disk."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

# === Summarization ===
def summarize_file(path):
    """Summarize the contents of a file using the LLM and log the summary."""
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

# === Digest ===
def generate_digest(days=1):
    """Generate a digest of recent memory entries and write to outputs/digest.txt."""
    log_path = os.path.join(MEMORY_DIR, "log.jsonl")
    if not os.path.exists(log_path):
        print("❌ No memory log found.")
        return
    cutoff = datetime.utcnow() - timedelta(days=days)
    with open(log_path, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f]
    recent = [e for e in entries if datetime.fromisoformat(e["timestamp"]) > cutoff]
    if not recent:
        print("⚠️ No recent memory entries.")
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    digest_path = os.path.join(OUTPUT_DIR, "digest.txt")
    digest = "\n\n".join(f"[{e['timestamp']}] {e['summary']}" for e in recent)
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write(digest)
    print(f"✅ Digest written to {digest_path}")

# === Ask Engine ===
def ask_question(question):
    """
    Search memory for relevant entries and use the LLM to answer a question.
    Returns the LLM's answer as a string.
    """
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
                print(chunk, end="", flush=True)
                chunks.append(chunk)
        except Exception as e:
            print(f"\n⚠️ Skipping invalid chunk: {e}", flush=True)
    t2 = time.time()
    print(f"\n[⏱️] Memory search: {t1-t0:.2f}s | LLM: {t2-t1:.2f}s | Total: {t2-t0:.2f}s", flush=True)
    answer = "".join(chunks).strip()
    return answer if answer else "⚠️ No answer generated."

# === Workspace Watcher ===
def is_valid_file_path(path):
    """Check if a path is a valid file path for tracking."""
    return ("/" in path or "\\" in path) and not path.strip().lower().startswith("d:") and not path.strip().startswith("python ")

def sync_workspace(path=WORKSPACE_DIR):
    """
    Scan the workspace directory, summarize changed files, and update memory state.
    Also logs deletions.
    """
    print("🔄 Syncing all modified files in workspace...")
    state = load_file_state()
    existing_paths = set()
    for root, _, files in os.walk(path):
        for file in files:
            if any(file.endswith(ext) for ext in IGNORED_EXTENSIONS):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, start=".").replace("\\", "/")
            existing_paths.add(rel_path)
    for key in list(state.keys()):
        if key not in existing_paths:
            print(f"🗑️ Removing deleted file from state: {key}")
            del state[key]
            log_event("File was deleted", key, event_type="deleted")
    for rel_path in existing_paths:
        full_path = os.path.join(".", rel_path)
        try:
            current_mtime = round(os.path.getmtime(full_path), 6)
        except FileNotFoundError:
            continue
        last_mtime = round(state.get(rel_path, 0), 6)
        print(f"⏱️  {rel_path} | last: {last_mtime}, current: {current_mtime}")
        if current_mtime > last_mtime:
            print(f"📄 Syncing updated file: {rel_path}")
            summarize_file(full_path)
            if is_valid_file_path(rel_path):
                state[rel_path] = current_mtime
        else:
            print(f"✅ Skipping unchanged file: {rel_path}")
    save_file_state(state)
    print("✅ Sync complete.")

class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events for the workspace watcher."""
    def on_modified(self, event):
        if event.is_directory or event.src_path.endswith(tuple(IGNORED_EXTENSIONS)):
            return
        rel_path = os.path.relpath(event.src_path, start=".").replace("\\", "/")
        print(f"🔄 Detected change in: {rel_path}")
        summarize_file(event.src_path)
        state = load_file_state()
        try:
            mtime = os.path.getmtime(event.src_path)
            if is_valid_file_path(rel_path):
                state[rel_path] = mtime
                save_file_state(state)
        except FileNotFoundError:
            pass
    def on_deleted(self, event):
        if event.is_directory:
            return
        rel_path = os.path.relpath(event.src_path, start=".").replace("\\", "/")
        print(f"❌ Detected deletion: {rel_path}")
        state = load_file_state()
        if rel_path in state:
            del state[rel_path]
            save_file_state(state)
            print(f"🗑️ Removed {rel_path} from last_seen.json")
            log_event("File was deleted", rel_path, event_type="deleted")

def start_file_watcher():
    """Start the workspace file watcher and sync on startup."""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    sync_workspace(WORKSPACE_DIR)
    observer = Observer()
    observer.schedule(FileChangeHandler(), path=WORKSPACE_DIR, recursive=True)
    observer.start()
    print("✅ Watching workspace/ for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# === ChromaDB Cleanup ===
def cleanup_chromadb(db_path="./chromadb"):
    """Delete the ChromaDB directory for a clean state."""
    if os.path.exists(db_path):
        import shutil
        shutil.rmtree(db_path)
        print(f"ChromaDB at {db_path} cleaned up.")
    else:
        print(f"No ChromaDB found at {db_path}.")