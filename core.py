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
try:
    from sentence_transformers import SentenceTransformer
    _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    def embed(text: str) -> list[float]:
        """Return a vector embedding for the given text."""
        return _embed_model.encode(text).tolist()
except ImportError:
    def embed(text: str) -> list[float]:
        raise ImportError("sentence-transformers not installed")

# === ChromaDB Memory Index (Lazy Initialization) ===
_chromadb_client = None
_chromadb_collection = None

def get_chromadb_collection():
    global _chromadb_client, _chromadb_collection
    if _chromadb_collection is None:
        import chromadb
        _chromadb_client = chromadb.PersistentClient(path="chromadb_store")
        _chromadb_collection = _chromadb_client.get_or_create_collection("memory")
    return _chromadb_collection

from config import (
    WORKSPACE_DIR, MEMORY_DIR, OUTPUT_DIR,
    LLM_MODEL, OLLAMA_API, MAX_TOKENS, IGNORED_EXTENSIONS
)

def add_memory(id: str, text: str, metadata: dict = {}):
    """Add a memory entry to the ChromaDB vector store."""
    try:
        collection = get_chromadb_collection()
    except ImportError:
        print("ChromaDB not available.")
        return
    embedding = embed(text)
    collection.add(
        documents=[text],
        ids=[id],
        embeddings=[embedding],
        metadatas=[metadata]
    )

def search_memory(query: str, top_k=10, where: dict = None):
    """Search memory entries using a vector query and optional metadata filter."""
    try:
        collection = get_chromadb_collection()
    except ImportError:
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
    try:
        collection = get_chromadb_collection()
    except ImportError:
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
    """
    Log a memory event (summary, deletion, etc.) to disk and ChromaDB.
    Standardizes event_type to "deletion" for deletions.
    """
    os.makedirs(MEMORY_DIR, exist_ok=True)
    if event_type.lower() in ("deleted", "deletion"):
        event_type = "deletion"
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source_path,
        "type": event_type,
        "summary": summary
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # Incremental update: add only this event to ChromaDB
    try:
        collection = get_chromadb_collection()
    except ImportError:
        return
    event_id = f"{entry['timestamp']}_{entry['source']}"
    add_memory(event_id, summary, metadata={
        "type": event_type,
        "timestamp": entry["timestamp"],
        "source": source_path
    })

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
    if not matches:
        print("[🗂️] No relevant memory entries found.")
        return "❌ No relevant memory entries found."

    print("\n[🗂️] Retrieved memory entries for LLM context:")
    for i, (summary, meta) in enumerate(matches, 1):
        print(f"{i}. [{meta.get('timestamp', meta.get('date', 'unknown'))}] ({meta.get('source', 'unknown')})\n   {summary}", flush=True)

    context = "\n\n".join(
        f"{i+1}. [{meta.get('timestamp', meta.get('date', 'unknown'))}] ({meta.get('source', 'unknown')})\n{summary}"
        for i, (summary, meta) in enumerate(matches)
    )

    prompt = (
        "You are an AI assistant. Below are memory log entries (context). "
        "Answer the user's question using ONLY the information in the context. "
        "Do not invent or assume any details that are not explicitly present. "
        "Do not reference external sources or users unless they are in the context. "
        "Do not skip any entry. Reference each entry as needed.\n\n"
        f"{context}\n\n"
        f"User's question: {question}\n"
        "Your answer (be thorough and reference all entries above):"
    )

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
            log_event("File was deleted", key, event_type="deletion")
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
            log_event("File was deleted", rel_path, event_type="deletion")

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
def cleanup_chromadb(db_path="chromadb_store"):
    """Delete the ChromaDB directory for a clean state."""
    if os.path.exists(db_path):
        import shutil
        shutil.rmtree(db_path)
        print(f"ChromaDB at {db_path} cleaned up.")
    else:
        print(f"No ChromaDB found at {db_path}.")

def resync_chromadb_from_log():
    """
    Delete ChromaDB and rebuild it from the log file.
    """
    cleanup_chromadb()
    log_path = os.path.join(MEMORY_DIR, "log.jsonl")
    if not os.path.exists(log_path):
        print("No memory log found for resync.")
        return
    # Wait a moment to ensure file handles are released
    time.sleep(1)
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            event_id = f"{entry['timestamp']}_{entry['source']}"
            add_memory(event_id, entry["summary"], metadata={
                "type": entry["type"],
                "timestamp": entry["timestamp"],
                "source": entry["source"]
            })
    print("ChromaDB has been fully resynced from log.")