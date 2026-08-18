# backend/ingest.py
"""
Careful ingestion pipeline: PDF -> structure-aware chunks (table-aware) -> Cohere embeddings -> Pinecone.

Adapted for "A System of Diagnosis in Outline" (Prof. Ashok Chandra) — this book's
structure differs from a typical clinical manual:
- Chapter/system titles (CARDIOLOGY, NEUROLOGY, etc.) use a distinctly larger font (>=18pt)
- Sub-section headings (A.1, B.2, D.1, etc.) are the SAME font size as body text —
  font-size detection can't catch these, so a regex pattern on the letter+number
  prefix convention is used instead.
- A small number of genuine gridded tables (onset/course/duration comparisons)
  are detected structurally via PyMuPDF's table detector.

Uses contextual embedding: each chunk's chapter+section is prepended to the text
before embedding (but NOT stored in the displayed text), so disease/topic names
from headings get baked into every sub-chunk's embedding even if the chunk's own
text never repeats them. This avoids terminology-mismatch retrieval misses.

Resumable: progress is checkpointed after every batch, so a rate-limit failure
never means starting the whole embed run over.

Usage:
    python ingest.py --pdf data/source.pdf --dry-run
    python ingest.py --pdf data/source.pdf --max-pages 20
    python ingest.py --pdf data/source.pdf
    python ingest.py --pdf data/source.pdf --reset   # ignore checkpoint, start fresh
"""
import argparse
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
import cohere
from pinecone import Pinecone, ServerlessSpec

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest")

BATCH_SIZE = 96
CHAPTER_FONT_MIN = 18.0          # chapter/section titles are reliably >=18pt in this book
TABLE_OVERLAP_THRESHOLD = 0.4
BATCH_PAUSE_SECONDS = 20

PROGRESS_FILE = Path("data/.ingest_progress.json")

# Matches: "A.1 SYMPTOMS...", "B.2  ETIOLOGICAL...", "D.  SYSTEM EXAMINATION", "B-2  CORRELATES"
LETTER_HEADING = re.compile(r"^([A-E])[\.\-]\s*(\d+)?\.?\s+([A-Z][A-Za-z /,\-()&']{2,90})$")
FI_LIGATURE_FIX = re.compile(r"([a-z])Ei")


def clean_ligature_artifacts(text: str) -> str:
    """Fixes PDF ligature decoding where 'fi' appears as 'Ei'."""
    text = FI_LIGATURE_FIX.sub(r"\1fi", text)
    text = re.sub(r"^Ei", "fi", text)
    return text


@dataclass
class Chunk:
    text: str
    page: int
    chapter: Optional[str] = None
    section: Optional[str] = None
    is_table_like: bool = False
    chunk_index: int = 0


# --- Resumability ---
def load_progress() -> int:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text()).get("next_chunk_index", 0)
    return 0


def save_progress(next_chunk_index: int):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps({"next_chunk_index": next_chunk_index}))


def clear_progress():
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()


# --- Table extraction ---
def table_to_text(table) -> str:
    """Converts a detected table to a clean markdown-style block, carrying
    forward merged/continuation cells."""
    rows = table.extract()
    if not rows:
        return ""
    lines = []
    header = [(c or "").replace("\n", " ").strip() for c in rows[0]]
    lines.append(" | ".join(header))
    lines.append(" | ".join("---" for _ in header))

    last_row = list(header)
    for row in rows[1:]:
        filled = []
        for i, cell in enumerate(row):
            if cell is None and i < len(last_row):
                filled.append(last_row[i])
            else:
                filled.append((cell or "").replace("\n", " ").strip())
        last_row = filled
        lines.append(" | ".join(filled))
    return "\n".join(lines)


def bbox_overlap_ratio(block_bbox, table_bbox) -> float:
    x0 = max(block_bbox[0], table_bbox[0]); y0 = max(block_bbox[1], table_bbox[1])
    x1 = min(block_bbox[2], table_bbox[2]); y1 = min(block_bbox[3], table_bbox[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    inter = (x1 - x0) * (y1 - y0)
    area = (block_bbox[2] - block_bbox[0]) * (block_bbox[3] - block_bbox[1])
    return inter / area if area > 0 else 0.0


def classify_block(text: str, max_size: float) -> str:
    """Returns 'chapter' | 'section' | 'para' for a non-table text block."""
    word_count = len(text.split())

    if max_size >= CHAPTER_FONT_MIN and word_count <= 8 and "\n" not in text:
        return "chapter"

    if "\n" not in text and LETTER_HEADING.match(text.strip()):
        return "section"

    return "para"


def extract_non_table_items(page: fitz.Page, table_bboxes: List[tuple]) -> List[dict]:
    items = []
    for block in page.get_text("dict")["blocks"]:
        lines = block.get("lines")
        if not lines:
            continue
        bbox = block.get("bbox")
        if any(bbox_overlap_ratio(bbox, tb) >= TABLE_OVERLAP_THRESHOLD for tb in table_bboxes):
            continue

        parts, max_size = [], 0.0
        for line in lines:
            t = "".join(s["text"] for s in line["spans"])
            if t.strip():
                parts.append(t)
            for s in line["spans"]:
                max_size = max(max_size, s["size"])
        text = "\n".join(parts).strip()
        if not text:
            continue
        text = clean_ligature_artifacts(text)

        kind = classify_block(text, max_size)
        items.append({"type": kind, "text": text, "y0": bbox[1]})
    return items


def build_page_item_stream(page: fitz.Page, page_num: int) -> List[dict]:
    tabs = page.find_tables()
    table_items = []
    for t in tabs.tables:
        text = table_to_text(t)
        if text.strip():
            table_items.append({"type": "table", "text": text, "y0": t.bbox[1], "page": page_num})

    table_bboxes = [t.bbox for t in tabs.tables]
    text_items = extract_non_table_items(page, table_bboxes)
    for it in text_items:
        it["page"] = page_num

    return sorted(table_items + text_items, key=lambda x: x["y0"])


def pack_into_chunks(
    paragraph_stream: List[Tuple[str, int, Optional[str], Optional[str]]],
    chunk_size: int,
) -> List[Chunk]:
    chunks: List[Chunk] = []
    current: List[str] = []
    current_len = 0
    current_page = current_chapter = current_section = None

    def flush():
        if current:
            text = "\n\n".join(current)
            chunks.append(Chunk(text=text, page=current_page, chapter=current_chapter, section=current_section))

    for text, page, chapter, section in paragraph_stream:
        if current and (current_len + len(text) > chunk_size or section != current_section):
            flush()
            current, current_len = [], 0
        current_page, current_chapter, current_section = page, chapter, section
        current.append(text)
        current_len += len(text)

    flush()
    return chunks


def load_and_chunk(pdf_path: str, max_pages: Optional[int] = None) -> List[Chunk]:
    logger.info(f"Loading PDF: {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF: {e}")
        sys.exit(1)

    total_pages = len(doc) if not max_pages else min(max_pages, len(doc))
    logger.info(f"Processing {total_pages} pages")

    paragraph_stream: List[Tuple[str, int, Optional[str], Optional[str]]] = []
    table_chunks: List[Chunk] = []
    current_chapter, current_section = None, None

    for i in range(total_pages):
        page_num = i + 1
        items = build_page_item_stream(doc[i], page_num)

        for item in items:
            if item["type"] == "chapter":
                current_chapter = item["text"]
                current_section = None
            elif item["type"] == "section":
                current_section = item["text"]
            elif item["type"] == "table":
                table_chunks.append(Chunk(
                    text=item["text"], page=item["page"],
                    chapter=current_chapter, section=current_section, is_table_like=True,
                ))
            else:  # para
                if len(item["text"]) >= settings.min_chunk_chars:
                    paragraph_stream.append((item["text"], item["page"], current_chapter, current_section))

    text_chunks = pack_into_chunks(paragraph_stream, settings.chunk_size)
    all_chunks = sorted(table_chunks + text_chunks, key=lambda c: (c.page,))

    for i, c in enumerate(all_chunks):
        c.chunk_index = i

    doc.close()
    return all_chunks


def report_stats(chunks: List[Chunk]):
    if not chunks:
        logger.warning("No chunks produced — check the PDF path/content.")
        return

    sizes = [len(c.text) for c in chunks]
    table_count = sum(1 for c in chunks if c.is_table_like)
    sections = {c.section for c in chunks if c.section}
    chapters = {c.chapter for c in chunks if c.chapter}

    logger.info("=" * 50)
    logger.info(f"Total chunks: {len(chunks)}")
    logger.info(f"Avg chunk size: {sum(sizes) / len(sizes):.0f} chars")
    logger.info(f"Min/Max chunk size: {min(sizes)} / {max(sizes)} chars")
    logger.info(f"Table chunks (kept intact): {table_count}")
    logger.info(f"Distinct chapters detected: {len(chapters)}")
    logger.info(f"Distinct sections detected: {len(sections)}")
    if chapters:
        logger.info(f"Chapters: {sorted(chapters)}")
    logger.info("=" * 50)


def embed_batch(co: cohere.Client, texts: List[str], retries: int = 2) -> List[List[float]]:
    for attempt in range(1, retries + 1):
        try:
            resp = co.embed(texts=texts, model=settings.cohere_embed_model, input_type="search_document")
            return resp.embeddings
        except Exception as e:
            wait = 30 * attempt
            logger.warning(f"Embed batch failed (attempt {attempt}/{retries}): {e}. Retrying in {wait}s")
            time.sleep(wait)
    logger.error("Embed batch failed after all retries")
    sys.exit(1)


def ensure_index(pc: Pinecone):
    existing = [idx["name"] for idx in pc.list_indexes()]
    if settings.pinecone_index_name not in existing:
        logger.info(f"Creating Pinecone index '{settings.pinecone_index_name}'")
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embed_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
        while not pc.describe_index(settings.pinecone_index_name).status["ready"]:
            time.sleep(1)
    else:
        logger.info(f"Using existing index '{settings.pinecone_index_name}'")
    return pc.Index(settings.pinecone_index_name)


def upsert_chunks(index, co: cohere.Client, chunks: List[Chunk], source_name: str):
    total = len(chunks)
    start_from = load_progress()
    if start_from > 0:
        logger.info(f"Resuming from chunk {start_from}/{total}")

    for start in range(start_from, total, BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        # Contextual embedding: prepend chapter+section so the disease/system name
        # is baked into every sub-chunk's embedding, even short ones. Display text
        # (stored in metadata) stays clean, without this prefix.
        embed_texts = [f"{c.chapter or ''} - {c.section or ''}\n\n{c.text}" for c in batch]
        embeddings = embed_batch(co, embed_texts)

        vectors = []
        for c, emb in zip(batch, embeddings):
            vectors.append({
                "id": f"chunk-{c.chunk_index}",
                "values": emb,
                "metadata": {
                    "text": c.text,
                    "page": c.page,
                    "chapter": c.chapter or "unknown",
                    "section": c.section or "unknown",
                    "chunk_index": c.chunk_index,
                    "char_count": len(c.text),
                    "is_table_like": c.is_table_like,
                    "source": source_name,
                },
            })

        try:
            index.upsert(vectors=vectors)
        except Exception as e:
            logger.error(f"Upsert failed for batch starting at {start}: {e}")
            sys.exit(1)

        next_index = min(start + BATCH_SIZE, total)
        save_progress(next_index)
        logger.info(f"Upserted {next_index}/{total} chunks")
        if next_index < total:
            time.sleep(BATCH_PAUSE_SECONDS)

    logger.info("All chunks upserted — clearing progress checkpoint.")
    clear_progress()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default="data/source.pdf")
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset", action="store_true", help="Ignore any saved checkpoint and start from chunk 0")
    args = parser.parse_args()

    if args.reset:
        clear_progress()
        logger.info("Checkpoint cleared — starting fresh.")

    chunks = load_and_chunk(args.pdf, max_pages=args.max_pages)
    report_stats(chunks)

    if args.dry_run:
        logger.info("Dry run complete — no embeddings or upserts performed.")
        for c in chunks:
            if c.is_table_like:
                logger.info(f"--- Sample TABLE chunk (page {c.page}, chapter={c.chapter}) ---")
                logger.info(c.text[:400])
                break
        for c in chunks[10:14]:
            logger.info(f"--- Sample chunk (page {c.page}, chapter={c.chapter}, section={c.section}, table={c.is_table_like}) ---")
            logger.info(c.text[:250])
        return

    co = cohere.Client(settings.cohere_api_key)
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = ensure_index(pc)

    upsert_chunks(index, co, chunks, source_name=args.pdf)
    logger.info("Ingestion complete.")


if __name__ == "__main__":
    main()