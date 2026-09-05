from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = Path(__file__).resolve().parent.parent.parent / "chroma_db"
FAQ_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "product_faq.txt"
COLLECTION_NAME = "bistro_faq"

def load_and_chunk_faq(faq_path: Path) -> list[dict]:
    if not faq_path.exists():
        raise FileNotFoundError(f"FAQ file not found at {faq_path}")

    with open(faq_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Split by double newline followed by "Q: " to maintain atomic Q&A boundaries
    sections = raw_text.split("\n\n")
    chunks = []
    chunk_index = 1

    for section in sections:
        cleaned = section.strip()
        # Filter out headers or empty splits
        if cleaned and cleaned.startswith("Q:"):
            chunks.append({
                "id": f"faq_chunk_{chunk_index:03d}",
                "text": cleaned
            })
            chunk_index += 1

    return chunks

def build_vector_store():
    chunks = load_and_chunk_faq(FAQ_PATH)
    print(f"Extracted {len(chunks)} Q&A chunks from {FAQ_PATH}")

    # Initialize persistent Chroma client
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    
    # Use standard default sentence-transformer embedding function
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    # Recreate collection cleanly
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )

    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]

    collection.add(
        ids=ids,
        documents=documents
    )
    print(f"Successfully indexed {len(documents)} chunks into collection '{COLLECTION_NAME}' at {CHROMA_PATH}")

if __name__ == "__main__":
    build_vector_store()