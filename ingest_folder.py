#!/usr/bin/env python3
"""
Engram Folder Ingestion Demo
============================

Point this at ANY folder and watch Engram build a knowledge graph from it.
Supports: .txt, .md, .py, .js, .ts, .json, .yaml, .toml, .html, .rst, .csv

Usage:
    # Ingest a folder (requires ENGRAM_EXTRACTION_API_KEY for LLM extraction)
    python ingest_folder.py /path/to/your/folder

    # Use the engram repo itself (no API key needed — uses pre-extracted facts)
    python ingest_folder.py . --no-llm

    # Compare engram vs naive search
    python ingest_folder.py /path/to/folder --compare "your search query"

Good datasets to try:
    • Paul Graham essays:  https://github.com/yishan/pg-essays (clone it, point here)
    • Enron emails:        kaggle.com/datasets/wcukierski/enron-email-dataset
    • Your own code:       python ingest_folder.py .
    • Obsidian/Notion:     export as markdown, point here
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
import webbrowser
from pathlib import Path

# Text extensions we can read
TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".yaml", ".yml", ".toml", ".html", ".htm", ".csv", ".sh", ".go",
    ".java", ".rb", ".rs", ".c", ".cpp", ".h", ".swift", ".kt", ".scala",
}

MAX_FILE_SIZE_KB = 64   # skip huge files
MAX_FILES = 200         # cap to keep demo fast


def _read_folder(folder: Path) -> list[tuple[Path, str]]:
    """Walk folder and return (path, content) for readable text files."""
    files = []
    for path in sorted(folder.rglob("*")):
        if path.is_dir():
            continue
        # Skip hidden dirs/files
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.stat().st_size > MAX_FILE_SIZE_KB * 1024:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            continue
        if len(content) < 50:  # skip near-empty files
            continue
        files.append((path, content))
        if len(files) >= MAX_FILES:
            break
    return files


def _detect_entity_type(path: Path) -> str:
    """Guess the entity type from file extension."""
    ext = path.suffix.lower()
    if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rs", ".c", ".cpp", ".h", ".swift", ".kt"):
        return "code"
    if ext in (".md", ".markdown", ".rst", ".txt"):
        return "document"
    if ext in (".json", ".yaml", ".yml", ".toml"):
        return "document"
    if ext in (".html", ".htm"):
        return "webpage"
    if ext == ".csv":
        return "document"
    return "file"


async def run_with_llm(folder: Path, compare_query: str | None, storage_path: Path):
    """Full pipeline: read folder → LLM extraction → graph → visualize."""
    from engram.config import EngramConfig
    from engram.client import MemoryClient
    from engram.viz.graph_view import visualize_user_graph

    api_key = os.environ.get("ENGRAM_EXTRACTION_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("  ERROR: Set ENGRAM_EXTRACTION_API_KEY or OPENAI_API_KEY for LLM extraction.")
        print("         Or run with --no-llm to use pre-extracted facts.")
        sys.exit(1)

    config = EngramConfig.from_env(
        local=True,
        storage_path=str(storage_path),
        extraction_api_key=api_key,
        extraction_model="gpt-4.1-nano",
    )

    files = _read_folder(folder)
    if not files:
        print(f"  No readable text files found in: {folder}")
        sys.exit(1)

    print(f"  Found {len(files)} files to ingest")

    client = MemoryClient(config=config)
    user_id = "demo_user"
    total_entities = 0
    total_rels = 0

    print(f"\n[2/{4 if compare_query else 3}] Ingesting files into knowledge graph...")
    t0 = time.time()

    for i, (path, content) in enumerate(files):
        etype = _detect_entity_type(path)
        rel_path = path.relative_to(folder)
        # Prepend filename context so LLM knows what it's reading
        text = f"File: {rel_path}\nType: {etype}\n\n{content[:3000]}"

        result = await client.add(
            text=text,
            user_id=user_id,
            session_id=f"ingest_{etype}",
        )
        total_entities += result.entities_created
        total_rels += result.relationships_created

        # Progress bar
        pct = int((i + 1) / len(files) * 40)
        bar = "█" * pct + "░" * (40 - pct)
        print(f"\r  [{bar}] {i+1}/{len(files)} files", end="", flush=True)

    elapsed = time.time() - t0
    print(f"\n  ✓ {total_entities} entities, {total_rels} relationships in {elapsed:.1f}s")

    await _visualize_and_search(client, user_id, storage_path, compare_query, step_offset=2)
    await client.close()


async def run_no_llm(folder: Path, compare_query: str | None, storage_path: Path):
    """Pre-extract facts from folder metadata (no LLM needed) for quick demo."""
    from engram.config import EngramConfig
    from engram.storage.kuzu_backend import KuzuBackend
    from engram.storage.lancedb_backend import LanceDBBackend
    from engram.storage.metadata_backend import MetadataBackend
    from engram.ingestion.embedder import Embedder
    from engram.ingestion.resolver import EntityResolver
    from engram.ingestion.temporal_linker import TemporalLinker
    from engram.retrieval.engine import RetrievalEngine
    from engram.types import Fact
    from engram.viz.graph_view import visualize_user_graph

    config = EngramConfig(
        local=True,
        storage_path=str(storage_path),
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
    )

    files = _read_folder(folder)
    if not files:
        print(f"  No readable text files found in: {folder}")
        sys.exit(1)

    print(f"  Found {len(files)} files to ingest (no-LLM mode)")

    graph = KuzuBackend(config)
    await graph.initialize()
    vector = LanceDBBackend(config)
    await vector.initialize()
    metadata_db = MetadataBackend(config)
    await metadata_db.initialize()
    embedder = Embedder(config)

    print("  ✓ Storage backends ready")

    user_id = "demo_user"
    tenant_id = "default"
    await metadata_db.ensure_tenant(tenant_id)
    await metadata_db.ensure_user(user_id, tenant_id)

    print(f"\n[2/{4 if compare_query else 3}] Building graph from file metadata...")
    t0 = time.time()

    # Group files by type and directory to build structure facts
    facts: list[Fact] = []
    type_counts: dict[str, int] = {}

    for path, content in files:
        etype = _detect_entity_type(path)
        rel_path = str(path.relative_to(folder))
        type_counts[etype] = type_counts.get(etype, 0) + 1

        # File node connected to its directory
        parent = str(path.parent.relative_to(folder)) if path.parent != folder else "root"
        file_name = f"{etype.upper()}: {rel_path}"

        # File → parent dir
        if parent != "root":
            facts.append(Fact(
                subject=file_name, subject_type=etype,
                predicate="part_of", object=f"DIR: {parent}", object_type="project",
                confidence=0.99, reasoning=f"File located in {parent}/",
            ))

        # Extract simple word-frequency topics from content (no LLM)
        words = [w.lower().strip(".,;:!?\"'()[]{}") for w in content.split()
                 if len(w) > 5 and w.isalpha()]
        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        top_words = sorted(freq.items(), key=lambda x: -x[1])[:3]

        for word, _ in top_words:
            facts.append(Fact(
                subject=file_name, subject_type=etype,
                predicate="mentioned", object=word, object_type="concept",
                confidence=0.60, reasoning=f"Frequent term in {rel_path}",
            ))

    # Add folder-level summary facts
    for etype, count in type_counts.items():
        facts.append(Fact(
            subject=folder.name, subject_type="project",
            predicate="contains", object=f"{count} {etype} files", object_type="concept",
            confidence=0.95, reasoning="File type distribution",
        ))

    # Resolve and ingest
    resolver = EntityResolver(config, graph, embedder)
    linker = TemporalLinker(graph)

    resolved = await resolver.resolve(facts, user_id, tenant_id, "folder_ingest")
    new_entities, new_rels, conflicts = await linker.link(resolved, "folder_ingest")

    for entity in new_entities:
        await graph.create_entity(entity)
        if entity.embedding:
            await vector.upsert(
                entity_id=entity.id, user_id=entity.user_id,
                tenant_id=entity.tenant_id, embedding=entity.embedding,
                summary=entity.summary, entity_type=entity.entity_type,
            )
    for rel in new_rels:
        await graph.create_relationship(rel)

    elapsed = time.time() - t0
    print(f"  ✓ {len(new_entities)} entities, {len(new_rels)} relationships in {elapsed:.1f}s")

    if compare_query:
        await _compare_retrieval(
            query=compare_query,
            files=files,
            engine=RetrievalEngine(config=config, graph=graph, vector=vector, embedder=embedder),
            user_id=user_id,
        )

    # Visualize
    step = 4 if compare_query else 3
    print(f"\n[{step}/{step}] Generating interactive knowledge graph visualization...")
    output_path = str(storage_path / "engram_graph.html")
    await visualize_user_graph(
        graph_backend=graph,
        user_id=user_id,
        tenant_id=tenant_id,
        output_path=output_path,
    )
    abs_path = str(Path(output_path).resolve())
    print(f"  ✓ Graph saved → {abs_path}")
    print(f"  ✓ {len(new_entities)} nodes, {len(new_rels)} edges")

    print(f"\n[{step}/{step}] Opening graph in browser...")
    webbrowser.open(f"file://{abs_path}")

    print("\n" + "=" * 60)
    print("  Done! Interact: zoom, pan, hover nodes, drag to rearrange")
    print(f"  Graph: {abs_path}")
    print("=" * 60 + "\n")

    await graph.close()
    await vector.close()
    await metadata_db.close()


async def _visualize_and_search(client, user_id, storage_path, compare_query, step_offset):
    from engram.viz.graph_view import visualize_user_graph

    if compare_query:
        step = step_offset + 1
        print(f"\n[{step}/4] Comparing engram vs naive search...")
        await _compare_retrieval_client(client, compare_query, user_id)

    step = step_offset + (2 if compare_query else 1)
    print(f"\n[{step}/{step}] Generating visualization...")
    output_path = str(storage_path / "engram_graph.html")
    await visualize_user_graph(
        graph_backend=client._graph,
        user_id=user_id,
        output_path=output_path,
    )
    abs_path = str(Path(output_path).resolve())
    print(f"  ✓ Graph saved → {abs_path}")
    webbrowser.open(f"file://{abs_path}")
    print("\n  Done! Graph opened in browser.\n")


async def _compare_retrieval(query: str, files: list[tuple[Path, str]], engine, user_id: str):
    """Show engram hybrid retrieval vs naive keyword search side-by-side."""
    print(f"\n[3/4] Comparing retrieval for: \"{query}\"\n")

    # Naive search: simple keyword grep over raw file content
    print("  ── NAIVE (keyword grep) ─────────────────────────────────────")
    query_words = set(query.lower().split())
    naive_hits = []
    for path, content in files:
        matches = sum(1 for w in query_words if w in content.lower())
        if matches > 0:
            naive_hits.append((path, matches, content[:150].replace("\n", " ")))
    naive_hits.sort(key=lambda x: -x[1])

    if naive_hits:
        for path, score, preview in naive_hits[:5]:
            print(f"  [{score} matches] {path.name}")
            print(f"    {preview}...")
    else:
        print("  (no keyword matches found)")

    print()

    # Engram hybrid retrieval
    print("  ── ENGRAM (vector + graph + temporal fusion) ─────────────────")
    t0 = time.time()
    ctx = await engine.search(query=query, user_id=user_id)
    ms = (time.time() - t0) * 1000

    if ctx.text:
        # Show top blocks
        blocks = ctx.text.split("\n\n")[:5]
        for block in blocks:
            print(f"  {block[:200].replace(chr(10), ' ')}")
    else:
        print("  (no results — try ingesting more data or a different query)")

    print(f"\n  Engram retrieved in {ms:.0f}ms | {ctx.total_tokens} tokens | "
          f"{ctx.retrieval_metadata.get('blocks_returned', 0)} blocks")
    print()
    print("  WHY ENGRAM IS BETTER:")
    print("  • Keyword search returns files with word matches, not meaning")
    print("  • Engram finds related entities via graph traversal (multi-hop)")
    print("  • Temporal awareness surfaces recent facts over stale ones")
    print("  • Hybrid fusion combines vector similarity + graph structure")


async def _compare_retrieval_client(client, query: str, user_id: str):
    print(f"  Query: \"{query}\"")
    t0 = time.time()
    ctx = await client.search(query=query, user_id=user_id)
    ms = (time.time() - t0) * 1000
    if ctx.text:
        print(f"  Engram result ({ms:.0f}ms):")
        print(f"  {ctx.text[:400].replace(chr(10), ' ')}...")
    else:
        print(f"  (no results in {ms:.0f}ms)")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a folder into Engram and visualize the knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("folder", help="Path to folder to ingest")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM extraction (faster, no API key needed)",
    )
    parser.add_argument(
        "--compare",
        metavar="QUERY",
        help='Compare engram vs naive search for this query (e.g. "What is this project about?")',
    )
    parser.add_argument(
        "--storage-path",
        default="./demo_data",
        help="Where to store the graph data (default: ./demo_data)",
    )
    args = parser.parse_args()

    folder = Path(args.folder).resolve()
    if not folder.exists():
        print(f"Error: folder not found: {folder}")
        sys.exit(1)
    if not folder.is_dir():
        print(f"Error: not a directory: {folder}")
        sys.exit(1)

    storage_path = Path(args.storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  🧠 Engram — Folder Knowledge Graph")
    print("=" * 60)
    print(f"\n  Folder:  {folder}")
    print(f"  Mode:    {'no-LLM (fast)' if args.no_llm else 'LLM extraction'}")
    print(f"  Storage: {storage_path.resolve()}")
    if args.compare:
        print(f"  Compare: \"{args.compare}\"")

    print("\n[1/{}] Scanning folder...".format(4 if args.compare else 3))

    if args.no_llm:
        asyncio.run(run_no_llm(folder, args.compare, storage_path))
    else:
        asyncio.run(run_with_llm(folder, args.compare, storage_path))


if __name__ == "__main__":
    main()
