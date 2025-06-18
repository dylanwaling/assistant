import json
from datetime import datetime
import os

def log_event(summary, source_path):
    log_path = "memory/log.jsonl"
    os.makedirs("memory", exist_ok=True)

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source_path,
        "summary": summary
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(event) + "\n")
