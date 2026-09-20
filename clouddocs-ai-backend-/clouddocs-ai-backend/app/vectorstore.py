from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings

_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    # Loaded once per process, runs locally — no API cost, no external call.
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    return model.encode(texts, show_progress_bar=False).tolist()


def get_collection(document_id: str):
    return _client.get_or_create_collection(name=f"doc_{document_id}")


def index_chunks(document_id: str, chunks: list[str]) -> int:
    collection = get_collection(document_id)
    embeddings = embed_texts(chunks)
    ids = [f"{document_id}-{i}" for i in range(len(chunks))]
    metadatas = [{"chunk_index": i} for i in range(len(chunks))]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return len(chunks)


def query_chunks(document_id: str, question: str, top_k: int = 4):
    collection = get_collection(document_id)
    query_embedding = embed_texts([question])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

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
