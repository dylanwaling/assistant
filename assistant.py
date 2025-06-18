import os
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from summarizer import summarize_file

STATE_FILE = "memory/last_seen.json"

# Load previously tracked file modification times
def load_file_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Save updated state after summarizing
def save_file_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

# Sync all files in workspace that are new or modified since last seen
def sync_workspace(path="./workspace"):
    print("🔄 Syncing all modified files in workspace...")
    state = load_file_state()

    for root, _, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, start=".").replace("\\", "/")

            try:
                current_mtime = round(os.path.getmtime(full_path), 6)
            except FileNotFoundError:
                continue

            last_mtime = round(state.get(rel_path, 0), 6)

            # Debug info
            print(f"⏱️  {rel_path} | last: {last_mtime}, current: {current_mtime}")

            if current_mtime > last_mtime:
                print(f"📄 Syncing updated file: {rel_path}")
                summarize_file(full_path)
                state[rel_path] = current_mtime
            else:
                print(f"✅ Skipping unchanged file: {rel_path}")

    save_file_state(state)
    print("✅ Sync complete.")

# Watch for live file edits
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, start=".")
            print(f"🔄 Detected change in: {rel_path}")
            summarize_file(event.src_path)
            # Update state immediately
            state = load_file_state()
            try:
                mtime = os.path.getmtime(event.src_path)
                state[rel_path] = mtime
                save_file_state(state)
            except FileNotFoundError:
                pass

# Full watcher startup: sync first, then watch
def start_file_watcher():
    path = "./workspace"
    if not os.path.exists(path):
        os.makedirs(path)

    sync_workspace(path)

    observer = Observer()
    observer.schedule(FileChangeHandler(), path=path, recursive=True)
    observer.start()
    print("✅ Watching workspace/ for changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
