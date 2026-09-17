"""
Create Embeddings for Regulation Chunks.

Generates dense vector embeddings for any regulation_chunks in the database
that currently lack embeddings, using sentence-transformers (all-MiniLM-L6-v2,
384 dimensions), and stores them back into the pgvector column.

Usage:
    python scripts/create_embeddings.py [--model all-MiniLM-L6-v2] [--batch-size 32]

Requires:
    - sentence-transformers installed
    - PostgreSQL running with pgvector extension enabled
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/legal_metrology",
)

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DEFAULT_DIM = int(os.getenv("EMBEDDING_DIMENSION", "384"))


def get_unembedded_chunks(conn, limit: int = 500) -> list[tuple]:
    """Fetch chunks that do not yet have an embedding."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, text
        FROM regulation_chunks
        WHERE embedding IS NULL
        LIMIT %s
        """,
        (limit,),
    )
    return cur.fetchall()


def update_chunk_embeddings(conn, chunk_id_embedding_pairs: list[tuple]):
    """Update embedding vectors for given chunk IDs."""
    cur = conn.cursor()
    for chunk_id, embedding in chunk_id_embedding_pairs:
        embedding_str = "[" + ",".join(str(f) for f in embedding) + "]"
        cur.execute(
            """
            UPDATE regulation_chunks
            SET embedding = %s::vector
            WHERE id = %s
            """,
            (embedding_str, chunk_id),
        )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(
        description="Compute and store embeddings for regulation chunks in pgvector."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Sentence-transformers model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding computation (default: 32)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute embeddings without saving to database",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Embedding Generation for Regulation Chunks")
    print("=" * 60)
    print(f"Model:      {args.model}")
    print(f"Dimension:  {DEFAULT_DIM}")
    print(f"Batch size: {args.batch_size}")
    print(f"Dry run:    {args.dry_run}")
    print(f"Database:   {DATABASE_URL}")
    print()

    # Check dependencies
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers is not installed.")
        print("Install with: pip install sentence-transformers")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 is not installed.")
        print("Install with: pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Connected to PostgreSQL.")
    except Exception as exc:
        print(f"ERROR: Could not connect to database: {exc}")
        print("Ensure PostgreSQL is running and DATABASE_URL_SYNC is correct.")
        sys.exit(1)

    try:
        # Check how many chunks need embeddings
        chunks = get_unembedded_chunks(conn)
        print(f"Found {len(chunks)} chunks without embeddings.")

        if not chunks:
            print("All chunks already have embeddings. Nothing to do.")
            return

        print(f"Loading embedding model '{args.model}'...")
        model = SentenceTransformer(args.model)

        # Process in batches
        total_updated = 0
        for i in range(0, len(chunks), args.batch_size):
            batch = chunks[i: i + args.batch_size]
            texts = [c[1] for c in batch]
            ids = [c[0] for c in batch]

            embeddings = model.encode(texts, show_progress_bar=False)

            pairs = list(zip(ids, [e.tolist() for e in embeddings]))

            if not args.dry_run:
                update_chunk_embeddings(conn, pairs)
                total_updated += len(pairs)
                print(f"  Processed {total_updated}/{len(chunks)} chunks...")
            else:
                print(f"  [DRY RUN] Computed embeddings for {len(batch)} chunks.")

        if not args.dry_run:
            print(f"\nSuccessfully stored {total_updated} embeddings in pgvector.")
        else:
            print(f"\nDry run complete. No database changes made.")

    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
