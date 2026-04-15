import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


ROOT = Path(__file__).resolve().parent
BASE_DIR = ROOT / "data" / "base_agreement"
BASE_TEXT_FILE = BASE_DIR / "base_agreement.md"
BASE_META_FILE = BASE_DIR / "metadata.json"
BASE_ORIGINAL_FILE = BASE_DIR / "base_agreement_original"


def _ensure_dir() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def save_base_agreement(
    normalized_text: str,
    source_filename: str,
    original_bytes: bytes,
) -> Dict[str, Any]:
    _ensure_dir()
    BASE_TEXT_FILE.write_text(normalized_text, encoding="utf-8")
    BASE_ORIGINAL_FILE.write_bytes(original_bytes)

    metadata = {
        "source_filename": source_filename,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "char_count": len(normalized_text),
        "word_count": len(normalized_text.split()),
    }
    BASE_META_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def has_base_agreement() -> bool:
    return BASE_TEXT_FILE.exists() and BASE_META_FILE.exists()


def load_base_agreement_text() -> str:
    if not BASE_TEXT_FILE.exists():
        raise FileNotFoundError("Base agreement has not been uploaded yet.")
    return BASE_TEXT_FILE.read_text(encoding="utf-8")


def load_base_agreement_metadata() -> Optional[Dict[str, Any]]:
    if not BASE_META_FILE.exists():
        return None
    return json.loads(BASE_META_FILE.read_text(encoding="utf-8"))


def load_base_agreement() -> Tuple[str, Optional[Dict[str, Any]]]:
    text = load_base_agreement_text()
    metadata = load_base_agreement_metadata()
    return text, metadata
