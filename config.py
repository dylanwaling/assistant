# config.py
# Configuration constants for the assistant project.

# === Workspace and Output Directories ===

WORKSPACE_DIR = "./workspace"  # Directory to watch for file changes and sync
MEMORY_DIR = "./memory"        # Directory to store memory logs and state
OUTPUT_DIR = "./outputs"       # Directory to store generated digests and outputs

# === LLM (Language Model) Settings ===

LLM_MODEL = "tinyllama"        # Name of the LLM model to use for summarization and Q&A
OLLAMA_API = "http://localhost:11434/api/generate"  # URL for the Ollama API endpoint
MAX_TOKENS = 300               # Maximum number of tokens for LLM responses (summarization, etc.)

# === File Sync and Filtering Settings ===

IGNORED_EXTENSIONS = [
    ".gitattributes",          # Ignore Git attributes files
    ".gitignore"               # Ignore Git ignore files
]