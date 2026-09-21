import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)


def get_collection(document_id: str):
    # No embedding_function passed -> Chroma uses its built-in lightweight
    # ONNX MiniLM model automatically. This avoids installing torch/
    # sentence-transformers, which are too heavy for small free-tier
    # hosting (e.g. Render's 512MB free instances).
    return _client.get_or_create_collection(name=f"doc_{document_id}")


def index_chunks(document_id: str, chunks: list[str]) -> int:
    collection = get_collection(document_id)
    ids = [f"{document_id}-{i}" for i in range(len(chunks))]
    metadatas = [{"chunk_index": i} for i in range(len(chunks))]
    # Passing documents with no embeddings -> Chroma embeds them itself.
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def query_chunks(document_id: str, question: str, top_k: int = 4):
    collection = get_collection(document_id)
    results = collection.query(query_texts=[question], n_results=top_k)

    passages = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        passages.append({
            "text": doc,
            "chunk_index": meta.get("chunk_index", -1),
            "score": 1 - dist,  # convert distance to a similarity-like score
        })
    return passages

