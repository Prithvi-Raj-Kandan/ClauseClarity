from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMA_PERSIST_DIR = Path(__file__).resolve().parent / "chroma_stores"
BASE_AGREEMENT_COLLECTION = "base_agreement"


def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is required for embeddings.")
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        api_key=GOOGLE_API_KEY,
    )


def create_vector_store(
    chunks: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    persist_dir: Optional[str] = None,
):
    """Create in-memory or persistent vector store from chunks."""
    embeddings = get_embeddings_model()
    if persist_dir:
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        full_path = str(CHROMA_PERSIST_DIR / persist_dir)
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings,
            metadatas=metadatas,
            persist_directory=full_path,
        )
    else:
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings,
            metadatas=metadatas,
        )
    return vector_store


def load_vector_store(persist_dir: str):
    """Load persisted vector store from disk."""
    embeddings = get_embeddings_model()
    full_path = str(CHROMA_PERSIST_DIR / persist_dir)
    return Chroma(persist_directory=full_path, embedding_function=embeddings)


def semantic_similarity_score(base_text: str, vector_store) -> float:
    """Return normalized similarity in [0, 1] using Chroma distance."""
    docs_and_scores = vector_store.similarity_search_with_score(base_text, k=1)
    if not docs_and_scores:
        return 0.0
    _, distance = docs_and_scores[0]
    return 1.0 / (1.0 + max(distance, 0.0))