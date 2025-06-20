# utils.py
# Utility functions for workspace and database maintenance.

import os
import shutil

def cleanup_chromadb(db_path="./chromadb"):
    """
    Remove the ChromaDB directory and all its contents.

    Args:
        db_path (str): Path to the ChromaDB directory. Defaults to './chromadb'.

    This is useful for resetting or cleaning up the persistent vector database.
    """
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        print(f"ChromaDB at {db_path} cleaned up.")
    else:
        print(f"No ChromaDB found at {db_path}.")

def clear_temp(temp_dir="./temp"):
    """
    Remove the temporary directory and all its contents.

    Args:
        temp_dir (str): Path to the temp directory. Defaults to './temp'.

    Use this to clear out temporary files created during processing.
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Temp directory {temp_dir} cleared.")
    else:
        print(f"No temp directory found at {temp_dir}.")