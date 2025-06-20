import os
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from summarizer import summarize_file
from config import WORKSPACE_DIR, MEMORY_DIR, IGNORED_EXTENSIONS
from memory_engine import log_event

STATE_FILE = os.path.join(MEMORY_DIR, "last_seen.json")

def is_valid_file_path(path):
    # Accepts paths with slashes, not starting with a command or drive prompt
    return ("/" in path or "\\" in path) and not path.strip().lower().startswith("d:") and not path.strip().startswith("python ")

# Load previously tracked file modification times
def load_file_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Save updated state after summarizing
def save_file_state(state):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    # Filter out any keys that are not valid file paths
    filtered_state = {k: v for k, v in state.items() if is_valid_file_path(k)}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_state, f, indent=2)

# Scan entire workspace and sync any changes
def sync_workspace(path=WORKSPACE_DIR):
    print("🔄 Syncing all modified files in workspace...")
    state = load_file_state()
    existing_paths = set()

    for root, _, files in os.walk(path):
        for file in files:
            if any(file.endswith(ext) for ext in IGNORED_EXTENSIONS):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, start=".").replace("\\", "/")
            existing_paths.add(rel_path)

    # Remove deleted files
    for key in list(state.keys()):
        if key not in existing_paths:
            print(f"🗑️ Removing deleted file from state: {key}")
            del state[key]
            log_event("File was deleted", key, event_type="deleted")

    # Check all current files
    for rel_path in existing_paths:
        full_path = os.path.join(".", rel_path)
        try:
            current_mtime = round(os.path.getmtime(full_path), 6)
        except FileNotFoundError:
            continue  # file deleted mid-scan

        last_mtime = round(state.get(rel_path, 0), 6)
        print(f"⏱️  {rel_path} | last: {last_mtime}, current: {current_mtime}")

        if current_mtime > last_mtime:
            print(f"📄 Syncing updated file: {rel_path}")
            summarize_file(full_path)
            if is_valid_file_path(rel_path):
                state[rel_path] = current_mtime
        else:
            print(f"✅ Skipping unchanged file: {rel_path}")

    save_file_state(state)
    print("✅ Sync complete.")

# FileSystem watcher class
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or event.src_path.endswith(tuple(IGNORED_EXTENSIONS)):
            return

        rel_path = os.path.relpath(event.src_path, start=".").replace("\\", "/")
        print(f"🔄 Detected change in: {rel_path}")
        summarize_file(event.src_path)

        state = load_file_state()
        try:
            mtime = os.path.getmtime(event.src_path)
            if is_valid_file_path(rel_path):
                state[rel_path] = mtime
                save_file_state(state)
        except FileNotFoundError:
            pass

    def on_deleted(self, event):
        if event.is_directory:
            return

        rel_path = os.path.relpath(event.src_path, start=".").replace("\\", "/")
        print(f"❌ Detected deletion: {rel_path}")

        state = load_file_state()
        if rel_path in state:
            del state[rel_path]
            save_file_state(state)
            print(f"🗑️ Removed {rel_path} from last_seen.json")
            log_event("File was deleted", rel_path, event_type="deleted")

# Main watcher loop
def start_file_watcher():
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    sync_workspace(WORKSPACE_DIR)

    observer = Observer()
    observer.schedule(FileChangeHandler(), path=WORKSPACE_DIR, recursive=True)
    observer.start()
    print("✅ Watching workspace/ for changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()