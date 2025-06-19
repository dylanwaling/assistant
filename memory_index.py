import chromadb
from embedder import embed

# Connect using the new Client() interface (persistent)
client = chromadb.PersistentClient(path="chromadb_store")

# Create or load a collection
collection = client.get_or_create_collection("memory")

def add_memory(id: str, text: str, metadata: dict = {}):
    embedding = embed(text)
    collection.add(
        documents=[text],
        ids=[id],
        embeddings=[embedding],
        metadatas=[metadata]
    )

def search_memory(query: str, top_k=5):
    query_vector = embed(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )
    return list(zip(results["documents"][0], results["metadatas"][0]))

def list_all_memories():
    results = collection.get()
    if not results["documents"]:
        print("🧠 No memory entries found in the database.")
        return

    for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
        print(f"\n#{i+1}")
        print(f"[{meta.get('timestamp', 'unknown')}] ({meta.get('source', 'unknown')})")
        print(doc)
