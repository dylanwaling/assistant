# utils.py

import os
import shutil

# === ChromaDB Cleanup ===
def cleanup_chromadb(db_path="./chromadb"):
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        print(f"ChromaDB at {db_path} cleaned up.")
    else:
        print(f"No ChromaDB found at {db_path}.")

# === Temp File Utilities ===
def clear_temp(temp_dir="./temp"):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Temp directory {temp_dir} cleared.")
    else:
        print(f"No temp directory found at {temp_dir}.")