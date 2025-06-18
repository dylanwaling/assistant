import os
import json
from datetime import datetime

STATE_FILE = "memory/last_seen.json"
LOG_FILE = "memory/log.jsonl"

def log_event(summary, source_path, event_type="summary"):
    os.makedirs("memory", exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source_path,
        "type": event_type,
        "summary": summary
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def load_file_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_file_state(state):
    os.makedirs("memory", exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
