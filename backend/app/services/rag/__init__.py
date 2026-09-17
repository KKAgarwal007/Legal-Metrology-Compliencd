"""RAG Service package."""
from app.services.rag.rag_service import (
    search_legal_regulations,
    ingest_pdf_regulation,
    generate_embedding,
    generate_batch_embeddings,
    get_authoritative_rule_fallback
)

__all__ = [
    "search_legal_regulations",
    "ingest_pdf_regulation",
    "generate_embedding",
    "generate_batch_embeddings",
    "get_authoritative_rule_fallback"
]
