import json
import os
from memory_index import add_memory

LOG_FILE = "memory/log.jsonl"

def index_all_logs():
    if not os.path.exists(LOG_FILE):
        print("❌ No memory log found.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                entry = json.loads(line)
                summary = entry.get("summary", "").strip()
                source = entry.get("source", "unknown")
                timestamp = entry.get("timestamp", f"id-{i}")
                entry_id = f"{timestamp}_{source}"

                if summary:
                    add_memory(entry_id, summary, metadata={
                        "timestamp": timestamp,
                        "source": source
                    })
            except Exception as e:
                print(f"⚠️ Error at line {i}: {e}")

    print("✅ All summaries indexed into vector memory.")

if __name__ == "__main__":
    index_all_logs()
