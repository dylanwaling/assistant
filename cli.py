import typer
from assistant import start_file_watcher
from digest import generate_digest
from ask import ask_question

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
    answer = ask_question(question)
    print(answer)

if __name__ == "__main__":
    app()
