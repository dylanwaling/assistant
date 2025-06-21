# main.py
# Entry point for the assistant CLI using Typer.

import typer
import time
import subprocess
import sys

from core import (
    start_file_watcher,
    generate_digest,
    ask_question,
    cleanup_chromadb,
    resync_chromadb_from_log
)

app = typer.Typer()

@app.command()
def watch():
    """
    Start watching the workspace directory for file changes.
    This will sync and summarize files as they are modified or deleted.
    """
    start_file_watcher()

@app.command()
def digest():
    """
    Generate a daily summary (digest) from recent memory log entries.
    Output is written to the outputs/digest.txt file.
    """
    generate_digest()

@app.command()
def ask(question: str):
    """
    Ask the assistant a question.
    The assistant will search memory for relevant context and use the LLM to answer.
    """
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

@app.command()
def resyncdb():
    """
    Fully resync ChromaDB from the log.
    """
    from core import resync_chromadb_from_log
    resync_chromadb_from_log()

if __name__ == "__main__":
    app()