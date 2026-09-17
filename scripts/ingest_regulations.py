"""
Ingest Legal Regulations into PostgreSQL / pgvector.

Extracts text from a legal document (PDF), splits it into semantically
meaningful chunks, extracts metadata (document name, rule/section, page),
computes embeddings, and stores them in the regulation_chunks table for RAG retrieval.

Usage:
    python scripts/ingest_regulations.py --file <path_to_pdf> [--name <document_name>]

Example:
    python scripts/ingest_regulations.py \\
        --file data/regulations/lm_rules_2011.pdf \\
        --name "Legal Metrology (Packaged Commodities) Rules, 2011"
"""

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone

# Optional PyMuPDF import
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text page by page from a PDF file.

    Returns a list of dicts: [{"page": 1, "text": "..."}]
    """
    if not PYMUPDF_AVAILABLE:
        print("[WARN] PyMuPDF (fitz) is not installed. Install with: pip install PyMuPDF")
        print("       Running in dry-run mode without text extraction.")
        return []

    doc = fitz.open(file_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append({"page": page_num + 1, "text": text})
    doc.close()
    return pages


def chunk_text(pages: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    Split page text into chunks with overlap.

    TODO (Phase 6): Implement rule-aware semantic chunking that splits along
    Legal Metrology rule boundaries (Rule 6(1)(a), Rule 6(1)(b), etc.)
    rather than purely arbitrary character windows.
    """
    chunks = []
    chunk_index = 0

    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]

        words = text.split()
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text_str = " ".join(words[start:end])

            # Simple rule-detection heuristic (to be improved in Phase 6)
            rule_hint = None
            for line in chunk_text_str.split("\n"):
                line_clean = line.strip()
                if line_clean.lower().startswith("rule ") or "rule 6" in line_clean.lower():
                    rule_hint = line_clean[:50]
                    break

            chunks.append({
                "chunk_index": chunk_index,
                "text": chunk_text_str,
                "page": page_num,
                "rule": rule_hint,
                "section": None,
                "metadata": {
                    "word_count": len(words[start:end]),
                    "char_count": len(chunk_text_str),
                },
            })
            chunk_index += 1
            start += chunk_size - overlap

    return chunks


def compute_embeddings(chunks: list[dict], model_name: str = "all-MiniLM-L6-v2") -> list[list[float]]:
    """
    Compute dense vector embeddings for chunks using sentence-transformers.

    TODO (Phase 7): Connect to active pgvector pipeline and cache embeddings.
    """
    if not EMBEDDINGS_AVAILABLE:
        print("[WARN] sentence-transformers not installed. Install with: pip install sentence-transformers")
        print("       Embedding generation skipped.")
        return [None] * len(chunks)

    model = SentenceTransformer(model_name)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a legal regulation PDF into PostgreSQL + pgvector."
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the PDF file to ingest",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Document name (defaults to file name)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="2011",
        help="Document version or year",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=300,
        help="Target chunk size in words (default: 300)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk only, do not write to database",
    )

    args = parser.parse_args()

    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    doc_name = args.name or os.path.splitext(os.path.basename(file_path))[0]

    print("=" * 60)
    print("Legal Document Ingestion Pipeline")
    print("=" * 60)
    print(f"File:       {file_path}")
    print(f"Document:   {doc_name}")
    print(f"Version:    {args.version}")
    print(f"Chunk size: {args.chunk_size} words")
    print(f"Dry run:    {args.dry_run}")
    print()

    # Step 1: Extract text
    print("[1/4] Extracting text from PDF...")
    pages = extract_text_from_pdf(file_path)
    print(f"      Extracted {len(pages)} pages with text.")

    if not pages:
        print("[INFO] No pages extracted. Check PyMuPDF installation or file contents.")
        print("       TODO: Phase 6 will implement the full ingestion loop.")
        return

    # Step 2: Chunk text
    print(f"[2/4] Chunking text (size: {args.chunk_size} words)...")
    chunks = chunk_text(pages, chunk_size=args.chunk_size)
    print(f"      Created {len(chunks)} chunks.")

    # Step 3: Embeddings
    print("[3/4] Generating embeddings (all-MiniLM-L6-v2, 384 dimensions)...")
    embeddings = compute_embeddings(chunks)
    has_embeddings = any(e is not None for e in embeddings)
    print(f"      Embeddings generated: {'Yes' if has_embeddings else 'No (skipped)'}")

    # Step 4: Database storage
    print("[4/4] Storing in PostgreSQL (pgvector)...")
    if args.dry_run:
        print("      Dry-run requested — skipping database insert.")
    else:
        print("      TODO (Phase 6/7): Insert regulation record and chunks into database.")
        print(f"      Target: regulations (1 row) + regulation_chunks ({len(chunks)} rows)")

    print()
    print("Ingestion plan complete.")
    print(f"Summary: {len(pages)} pages -> {len(chunks)} chunks -> 384-d vectors")


if __name__ == "__main__":
    main()
