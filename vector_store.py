import chromadb
from chromadb.config import Settings

chroma_client = chromadb.Client(Settings(
    persist_directory="./vector_store",  # local storage path
    anonymized_telemetry=False           # disable telemetry for privacy
))

# Create or get your collection
collection = chroma_client.get_or_create_collection(name="memory")
