# main.py

import typer
import time
from core import (
    start_file_watcher, generate_digest, ask_question, cleanup_chromadb
)

app = typer.Typer()

@app.command()
def watch():
    """Watch the workspace folder for changes."""
    start_file_watcher()

@app.command()
def digest():
    """Generate a daily summary from memory."""
    generate_digest()

@app.command()
def ask(question: str):
    """Ask the assistant a question."""
    start_time = time.time()
    print("[⏳] Processing your question...")
    answer = ask_question(question)
    elapsed = time.time() - start_time
    print(f"\n[✅] Done in {elapsed:.2f} seconds.")
    print(answer)

@app.command()
def cleanupdb():
    """Cleanup ChromaDB."""
    cleanup_chromadb()

if __name__ == "__main__":
    app()