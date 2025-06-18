import json
import os
from datetime import datetime, timedelta
from config import MEMORY_DIR, OUTPUT_DIR

def generate_digest(days=1):
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
