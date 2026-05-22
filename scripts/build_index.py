from pathlib import Path
import logging
import os
import shutil
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings


os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)


def clean_chroma_index():
    chroma_dir = settings.CHROMA_DIR.resolve()
    storage_dir = settings.STORAGE_DIR.resolve()
    if not chroma_dir.is_relative_to(storage_dir):
        raise RuntimeError(f"Refusing to remove unexpected Chroma path: {chroma_dir}")
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)


def main():
    clean_chroma_index()
    from core.vector_store import vector_store

    counts = vector_store.build_all(reset=True)
    print("Local index build complete:")
    for name, count in counts.items():
        print(f"- {name}: {count}")
    if not vector_store.chroma_available:
        print(f"Warning: Chroma is not available. Fallback lexical search will be used. Reason: {vector_store.init_error}")


if __name__ == "__main__":
    main()
