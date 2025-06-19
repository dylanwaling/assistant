from sentence_transformers import SentenceTransformer

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text: str) -> list[float]:
    """Return a vector embedding for the given text."""
    return model.encode(text).tolist()
