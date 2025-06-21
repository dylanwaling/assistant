import os
import json
import time
from core import cleanup_chromadb, add_memory, MEMORY_DIR

def resync_chromadb_from_log():
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

if __name__ == "__main__":
    resync_chromadb_from_log()
    import subprocess
    print("Restarting assistant using launch_all.bat...")
    subprocess.Popen(["cmd", "/c", "start", "launch_all.bat"])