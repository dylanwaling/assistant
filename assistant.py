from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from summarizer import summarize_file
import time

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            summarize_file(event.src_path)

def start_file_watcher():
    path = "./workspace"
    observer = Observer()
    observer.schedule(FileChangeHandler(), path=path, recursive=True)
    observer.start()
    print("Watching workspace/ for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
