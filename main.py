# main.py
# Entry point for the assistant CLI using Typer.
# Exposes commands for watching the workspace, generating digests, asking questions, and cleaning up ChromaDB.

import typer
import time
from core import (
    start_file_watcher,    # Watches the workspace for file changes
    generate_digest,       # Generates a digest of recent memory entries
    ask_question,          # Asks the LLM a question using memory context
    cleanup_chromadb       # Cleans up the ChromaDB directory
)

# Create a Typer app for CLI commands
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

if __name__ == "__main__":
    # Run the Typer CLI app if this file is executed directly
    app()