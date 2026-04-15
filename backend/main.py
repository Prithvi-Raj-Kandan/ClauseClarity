import os
from typing import Any, Dict, List
import importlib.util
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .base_agreement_store import (
        has_base_agreement,
        load_base_agreement,
        load_base_agreement_metadata,
        save_base_agreement,
    )
    from .pdf_handler import extract_text_from_pdf_bytes, normalize_text, split_text
    from .ragchain import build_grounded_answer
    from .regex import RENTAL_AGREEMENT_SCHEMA, analyze_agreement_detailed
    from .vectorstore import create_vector_store, semantic_similarity_score, load_vector_store
except ImportError:
    from base_agreement_store import (  # type: ignore
        has_base_agreement,
        load_base_agreement,
        load_base_agreement_metadata,
        save_base_agreement,
    )
    from pdf_handler import extract_text_from_pdf_bytes, normalize_text, split_text  # type: ignore
    from ragchain import build_grounded_answer  # type: ignore
    from vectorstore import create_vector_store, semantic_similarity_score, load_vector_store  # type: ignore

    regex_path = Path(__file__).with_name("regex.py")
    spec = importlib.util.spec_from_file_location("clauseclarify_regex", regex_path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not load local regex.py module.")
    regex_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(regex_module)
    RENTAL_AGREEMENT_SCHEMA = regex_module.RENTAL_AGREEMENT_SCHEMA
    analyze_agreement_detailed = regex_module.analyze_agreement_detailed

load_dotenv()

ALLOWED_EXTENSIONS = {"pdf", "txt", "md"}
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI(title="ClauseClarify API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2)
    agreement_text: str = Field(..., min_length=20)
    analysis_summary: str = Field(default="")


def _ensure_embedding_ready() -> None:
    if not GOOGLE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is missing. Add it to your environment before using analysis/chat.",
        )


def _get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _extract_upload_text(upload: UploadFile, content: bytes) -> str:
    ext = _get_extension(upload.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    if ext == "pdf":
        extracted = extract_text_from_pdf_bytes(content)
    else:
        extracted = content.decode("utf-8", errors="ignore")

    normalized = normalize_text(extracted)
    if not normalized:
        raise HTTPException(status_code=400, detail="Could not extract usable text from file.")
    return normalized


def _build_analysis(uploaded_text: str, base_text: str, persist_upload: bool = False, upload_store_name: str = "latest_upload") -> Dict[str, Any]:
    details = analyze_agreement_detailed(uploaded_text)
    uploaded_chunks = split_text(uploaded_text)
    base_chunks = split_text(base_text)

    if not uploaded_chunks or not base_chunks:
        raise HTTPException(status_code=400, detail="Insufficient text to run semantic comparison.")

    uploaded_store = create_vector_store(
        uploaded_chunks,
        metadatas=[{"source": "uploaded"}] * len(uploaded_chunks),
        persist_dir=upload_store_name if persist_upload else None,
    )
    base_store = create_vector_store(base_chunks)

    semantic_scores: Dict[str, float] = {}
    for category, schema in RENTAL_AGREEMENT_SCHEMA.items():
        query = f"{category}. {schema['critical_check']}"
        base_match = base_store.similarity_search(query, k=1)
        if not base_match:
            semantic_scores[category] = 0.0
            continue
        semantic_scores[category] = round(
            semantic_similarity_score(base_match[0].page_content, uploaded_store),
            4,
        )

    critical_missing_count = len(details["critical_missing"])
    total_missing_count = len(details["missing_categories"])
    high_risk_flag_count = len(details.get("high_risk_flags", []))
    avg_similarity = sum(semantic_scores.values()) / max(len(semantic_scores), 1)

    if high_risk_flag_count >= 2 or critical_missing_count >= 2 or avg_similarity < 0.35:
        risk_level = "high"
    elif high_risk_flag_count >= 1 or critical_missing_count == 1 or total_missing_count >= 2 or avg_similarity < 0.55:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "missing_categories": details["missing_categories"],
        "critical_missing": details["critical_missing"],
        "high_risk_flags": details.get("high_risk_flags", []),
        "category_results": details["categories"],
        "semantic_similarity": semantic_scores,
        "summary": {
            "risk_level": risk_level,
            "critical_missing_count": critical_missing_count,
            "total_missing_count": total_missing_count,
            "high_risk_flag_count": high_risk_flag_count,
            "average_similarity": round(avg_similarity, 4),
        },
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/base-agreement/upload")
async def upload_base_agreement(file: UploadFile = File(...)) -> Dict[str, Any]:
    _ensure_embedding_ready()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded base agreement is empty.")

    normalized = _extract_upload_text(file, content)
    metadata = save_base_agreement(
        normalized_text=normalized,
        source_filename=file.filename or "base_agreement",
        original_bytes=content,
    )

    # Persist base agreement vector store for reuse
    base_chunks = split_text(normalized)
    if base_chunks:
        create_vector_store(
            base_chunks,
            metadatas=[{"source": "base"}] * len(base_chunks),
            persist_dir="base_agreement_store",
        )

    return {
        "message": "Base agreement uploaded and stored.",
        "metadata": metadata,
    }


@app.get("/base-agreement")
async def get_base_agreement() -> Dict[str, Any]:
    if not has_base_agreement():
        raise HTTPException(status_code=404, detail="Base agreement not found.")

    text, metadata = load_base_agreement()
    preview = text[:800]
    return {
        "metadata": metadata,
        "preview": preview,
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    _ensure_embedding_ready()
    if not has_base_agreement():
        raise HTTPException(
            status_code=400,
            detail="Upload a base agreement first via /base-agreement/upload.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded agreement is empty.")

    agreement_text = _extract_upload_text(file, content)
    base_text, base_meta = load_base_agreement()
    analysis = _build_analysis(agreement_text, base_text, persist_upload=True)

    return {
        "message": "Agreement analyzed successfully.",
        "base_agreement": base_meta or load_base_agreement_metadata(),
        "analysis": analysis,
        "agreement_text": agreement_text,
    }


@app.post("/chat")
async def chat(payload: ChatRequest) -> Dict[str, Any]:
    _ensure_embedding_ready()
    if not has_base_agreement():
        raise HTTPException(status_code=400, detail="Base agreement not found.")

    try:
        base_store = load_vector_store("base_agreement_store")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Base agreement embeddings not ready. Re-upload the base agreement.",
        )

    try:
        upload_store = load_vector_store("latest_upload")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="No user agreement analyzed yet. Upload an agreement first.",
        )

    retrieved = []
    try:
        base_retrieved = base_store.similarity_search_with_score(payload.question, k=3)
        for doc, score in base_retrieved:
            doc.metadata["source"] = "base"
            retrieved.append((doc, score))
    except Exception:
        pass

    try:
        upload_retrieved = upload_store.similarity_search_with_score(payload.question, k=3)
        for doc, score in upload_retrieved:
            doc.metadata["source"] = "uploaded"
            retrieved.append((doc, score))
    except Exception:
        pass

    retrieved_contexts: List[str] = []
    citations: List[Dict[str, Any]] = []

    for doc, distance in sorted(retrieved, key=lambda x: x[1])[:6]:
        source = doc.metadata.get("source", "unknown")
        snippet = doc.page_content[:300]
        retrieved_contexts.append(f"[{source}] {doc.page_content}")
        citations.append(
            {
                "source": source,
                "distance": round(float(distance), 4),
                "snippet": snippet,
            }
        )

    answer = build_grounded_answer(
        question=payload.question,
        retrieved_contexts=retrieved_contexts,
        analysis_summary=payload.analysis_summary,
    )

    return {
        "answer": answer,
        "citations": citations,
    }


