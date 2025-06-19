# config.py

# === Workspace Settings ===
WORKSPACE_DIR = "./workspace"
MEMORY_DIR = "./memory"
OUTPUT_DIR = "./outputs"

# === LLM Settings ===
LLM_MODEL = "llama3"
OLLAMA_API = "http://localhost:11434/api/generate"
MAX_TOKENS = 300  # optional: to limit summarizer response

# === Sync Settings ===
IGNORED_EXTENSIONS = [".gitattributes", ".gitignore"]