import json
from datetime import datetime, timedelta
import os

def generate_digest(days=1):
    log_path = "memory/log.jsonl"
    if not os.path.exists(log_path):
        print("No memory log found.")
        return

    cutoff = datetime.utcnow() - timedelta(days=days)
    with open(log_path, "r") as f:
        entries = [json.loads(line) for line in f]

    recent = [e for e in entries if datetime.fromisoformat(e["timestamp"]) > cutoff]

    if not recent:
        print("No recent entries.")
        return

    digest = "\n\n".join([f"[{e['timestamp']}] {e['summary']}" for e in recent])
    with open("outputs/digest.txt", "w") as f:
        f.write(digest)

    print("Digest written to outputs/digest.txt")
