import os
import json
from datetime import datetime
from config import MEMORY_DIR
from chromadb_cleanup import cleanup_chromadb  # <-- Add this import

STATE_FILE = os.path.join(MEMORY_DIR, "last_seen.json")
LOG_FILE = os.path.join(MEMORY_DIR, "log.jsonl")

def log_event(summary, source_path, event_type="summary"):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source_path,
        "type": event_type,
        "summary": summary
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    cleanup_chromadb()  # <-- Add this line

def load_file_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_file_state(state):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)