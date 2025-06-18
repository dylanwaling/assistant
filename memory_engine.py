import os
import json
from datetime import datetime

def log_event(summary, source_path):
    os.makedirs("memory", exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source_path,
        "summary": summary
    }
    with open("memory/log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
