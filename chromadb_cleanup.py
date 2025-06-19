import os
import json
from memory_index import collection

LOG_FILE = "memory/log.jsonl"

def get_log_ids():
    ids = set()
    if not os.path.exists(LOG_FILE):
        return ids
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                source = entry.get("source", "unknown")
                timestamp = entry.get("timestamp", "unknown")
                entry_id = f"{timestamp}_{source}"
                ids.add(entry_id)
            except Exception:
                continue
    return ids

def cleanup_chromadb():
    log_ids = get_log_ids()
    db = collection.get()
    db_ids = db["ids"] if "ids" in db else []
    to_remove = [id_ for id_ in db_ids if id_ not in log_ids]
    if to_remove:
        collection.delete(ids=to_remove)