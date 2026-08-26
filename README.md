# Engram

**Hybrid memory layer for AI agents** — combines knowledge graph traversal, vector similarity search, and temporal awareness into a single retrieval system that actually knows what changed, what matters, and when.

```python
from engram import MemoryClient

memory = MemoryClient(local=True)

# Store anything
await memory.add(text="We decided to use FastAPI instead of Django", user_id="alice")
await memory.add(text="Alice prefers async Python for all new services", user_id="alice")

# Retrieve with hybrid intelligence
ctx = await memory.search("What stack did we pick?", user_id="alice")
print(ctx.text)
# → "Alice decided on FastAPI (replaced Django). Prefers async Python."
```

**Live demo:** [engram.saalikahmed.com](https://engram.saalikahmed.com) — interactive pipeline walkthrough + knowledge graph explorer, no API keys needed.

---

## Why Engram?

| | Naive RAG | Mem0 | Zep | **Engram** |
|---|---|---|---|---|
| Vector search | ✅ | ✅ | ✅ | ✅ |
| Knowledge graph | ❌ | partial | ✅ | ✅ |
| Temporal versioning | ❌ | ❌ | partial | ✅ |
| Multi-hop traversal | ❌ | ❌ | ✅ | ✅ |
| Global / thematic search | ❌ | ❌ | ❌ | ✅ |
| Cross-encoder reranking | ❌ | ❌ | ❌ | ✅ |
| Multimodal (images, audio, PDF) | ❌ | ❌ | ❌ | ✅ |
| Fully local / embedded | ❌ | ❌ | ❌ | ✅ |
| Open source | — | partial | partial | ✅ |

### The core insight

When you ask *"what backend framework are we using?"*, a pure vector search returns documents that mention frameworks. Engram does this:

```
1. Vector search → FastAPI, Django, Flask (by similarity)
2. Graph traversal → Alice --[decided]--> FastAPI
                      Alice --[replaced]--> Django  ← temporal edge!
3. Temporal layer → FastAPI is active (today), Django was invalidated (last week)
4. Fusion → FastAPI scores 3x higher because it has multi-source corroboration
```

The result is *grounded context*, not just similar chunks.

---

## Architecture

```
                    ┌─────────────────────────────────────┐
    Input text      │         Ingestion Pipeline           │
    conversations ──►  preprocess → LLM extract → glean  │
    files, code     │  → resolve → temporal_link → store  │
                    └──────────┬──────────────┬────────────┘
                               │              │
                    ┌──────────▼──┐   ┌───────▼──────────┐
                    │  Kuzu Graph │   │  LanceDB Vectors  │
                    │  (entities +│   │  (ANN similarity) │
                    │   edges,    │   │   384 / 1536 /    │
                    │  versioned) │   │   3072-dim)        │
                    └──────────┬──┘   └───────┬───────────┘
                               │              │
                    ┌──────────▼──────────────▼────────────┐
                    │         Retrieval Engine              │
                    │  classify → parallel search →         │
                    │  weighted RRF fusion → (rerank) →     │
                    │  token-budget context assembly        │
                    └──────────────────────────────────────┘
```

**Storage:**
- **Kuzu** — embedded graph DB, append-only edges with `valid_from`/`invalid_from` for temporal versioning
- **LanceDB** — embedded vector store, ANN search over entity summaries
- **SQLite** (local) or **PostgreSQL** (cloud) — metadata, sessions, ingestion logs

**Embedding providers:**
- `all-MiniLM-L6-v2` — local, free, 384-dim (default)
- `text-embedding-3-small` — OpenAI, 1536-dim
- `gemini-embedding-2-preview` — Google, **3072-dim, multimodal** (text + images + audio + video + PDF)

---

## Install

```bash
pip install engram

# With Google multimodal embeddings
pip install "engram[google]"

# With MCP server support
pip install "engram[mcp]"
```

---

## Quick Start

### 1. Run the interactive demo (no API keys needed)

```bash
python demo.py
```

Ingests sample conversations, builds a knowledge graph, opens it in your browser.

### 2. Ingest your own folder

```bash
# Fast mode (no LLM, builds graph from file structure)
python ingest_folder.py /path/to/your/folder --no-llm

# Full LLM extraction (needs OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
python ingest_folder.py /path/to/your/folder

# Show engram vs naive search comparison
python ingest_folder.py /path/to/folder --no-llm --compare "what is this project about?"
```

**Good datasets to try:**
- **Paul Graham essays** — `git clone https://github.com/yishan/pg-essays` then point here
- **Your own codebase** — `python ingest_folder.py .`
- **Obsidian vault / Notion export** — export as markdown
- **Enron emails** — [Kaggle dataset](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset)

### 3. Use as a Python library

```python
import asyncio
from engram import MemoryClient

async def main():
    memory = MemoryClient(local=True)

    # Ingest conversation
    await memory.add(
        messages=[
            {"role": "user", "content": "I'm building a memory layer for AI agents"},
            {"role": "assistant", "content": "What stack are you using?"},
            {"role": "user", "content": "Kuzu for the graph, LanceDB for vectors"},
        ],
        user_id="alice",
        session_id="session_001",
    )

    # Hybrid search (default)
    ctx = await memory.search("What database is Alice using?", user_id="alice")
    print(ctx.text)

    # Global / thematic search — finds the most connected entities
    ctx = await memory.search("Give me an overview of this project", user_id="alice", mode="global")
    print(ctx.text)

    # Temporal history for a specific entity
    history = await memory.history(user_id="alice", entity_name="Kuzu")
    for v in history:
        print(f"{v.entity_name}: {v.relationship_summary}")

    await memory.close()

asyncio.run(main())
```

### 4. REST API

```bash
engram serve --port 8000
```

```bash
# Store memory
curl -X POST http://localhost:8000/v1/memories \
  -H "Content-Type: application/json" \
  -d '{"text": "Alice uses FastAPI", "user_id": "alice"}'

# Search
curl -X POST http://localhost:8000/v1/memories/search \
  -d '{"query": "what framework?", "user_id": "alice"}'
```

### 5. MCP server (Claude Desktop / Cursor)

```bash
engram serve --mcp
```

Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "engram": {
      "command": "engram",
      "args": ["serve", "--mcp"]
    }
  }
}
```

Tools exposed: `memory_search`, `memory_add`, `memory_history`, `memory_delete`

---

## Retrieval Modes

### Hybrid (default)

Three parallel search paths fused via weighted Reciprocal Rank Fusion:

| Query type | Vector | Graph | Temporal |
|---|---|---|---|
| Temporal ("when did we...") | 0.20 | 0.30 | **0.50** |
| Factual ("what is...") | 0.20 | **0.60** | 0.20 |
| Preference ("does Alice like...") | **0.50** | 0.30 | 0.20 |
| Default | 0.35 | 0.40 | 0.25 |

Entities found across multiple paths get a **1.15–1.30× multi-source bonus** before final ranking.

### Global

```python
ctx = await memory.search("What are the main themes?", user_id="alice", mode="global")
```

Triggered automatically by queries containing "overview", "themes", "what do you know about", or explicitly via `mode="global"`. Uses degree-centrality to find the most connected entities across the entire graph, then falls back to vector search for coverage. Good for summarization and broad orientation queries.

### Reranker (optional)

Enable a cross-encoder precision pass after RRF fusion:

```python
from engram import MemoryClient, EngramConfig

memory = MemoryClient(
    local=True,
    config=EngramConfig(reranker_model="BAAI/bge-reranker-v2-m3", reranker_top_k=30),
)
```

Downloads ~600MB on first use. Gives a measurable precision boost on factual queries at the cost of ~150ms latency.

---

## Ingestion Features

### Gleaning

After initial fact extraction, Engram runs a second LLM pass over its own output to catch missed facts. Controlled by `config.max_glean_rounds` (default `1`, set `0` to disable).

### Entity Resolution

Mentions like "FastAPI", "fast api", and "the FastAPI framework" are deduplicated into a single canonical node using:
- Fuzzy string matching (threshold 0.85)
- Embedding cosine similarity (threshold 0.92)

### Temporal Versioning

Contradicting facts are never overwritten. Every relationship has `valid_from` and optionally `invalid_from` timestamps. This means Engram can answer "what did Alice use *before* FastAPI?" correctly.

---

## Multimodal Embeddings

With Google Gemini, you can embed *anything*:

```python
from engram import MemoryClient

memory = MemoryClient(
    local=True,
    config=EngramConfig.from_env(
        google_api_key="...",
        embedding_model="gemini-embedding-2-preview",
    )
)

# Embed an image
embedding = await memory._embedder.embed_image("architecture.png")

# Embed a PDF
embedding = await memory._embedder.embed_file("spec.pdf")

# Embed text + image together
embedding = await memory._embedder.embed_multimodal(
    text="This diagram shows the ingestion pipeline",
    file_path="pipeline.png",
)
```

Supported: PNG, JPEG, GIF, WebP, PDF, MP4, MOV, AVI, MP3, WAV, FLAC

---

## Integrations

### LangChain

```python
from engram.integrations.langchain import MemoryRetriever, MemoryChatHistory

retriever = MemoryRetriever(client=memory, user_id="alice")
docs = retriever.invoke("What framework?")
```

### OpenAI Agents SDK

```python
from engram.integrations.openai_agents import memory_tools
from agents import Agent

agent = Agent(tools=memory_tools(memory, user_id="alice"))
```

---

## Visualize the Knowledge Graph

```bash
engram viz --user-id alice --output graph.html
```

Or from Python:

```python
from engram.viz.graph_view import visualize_user_graph

await visualize_user_graph(graph_backend=graph, user_id="alice", output_path="graph.html")
```

Opens an interactive graph with:
- **Circles** — persons, projects, tools, organizations
- **Squares** — documents, code files, images
- **Triangles** — conversations, webpages
- **Diamonds** — concepts, audio
- **Red edges** — high-signal decisions
- **Gray edges** — mentions
- **Dashed edges** — temporal conflicts/supersessions

---

## Configuration

All config via env vars or `EngramConfig`:

```bash
# Storage
ENGRAM_STORAGE_PATH=./my_data

# Embeddings
ENGRAM_EMBEDDING_MODEL=all-MiniLM-L6-v2        # local
ENGRAM_EMBEDDING_MODEL=text-embedding-3-small  # OpenAI
ENGRAM_EMBEDDING_MODEL=gemini-embedding-2-preview  # Google multimodal

# LLM extraction
ENGRAM_EXTRACTION_API_KEY=sk-...
ENGRAM_EXTRACTION_MODEL=gpt-4.1-nano

# Google (multimodal)
GOOGLE_API_KEY=...

# Cloud mode
ENGRAM_API_KEY=your-engram-api-key
ENGRAM_DATABASE_URL=postgresql://...
```

Key `EngramConfig` fields:

| Field | Default | Purpose |
|---|---|---|
| `max_glean_rounds` | `1` | LLM re-extraction passes (0 = off) |
| `reranker_model` | `None` | Cross-encoder model name (None = off) |
| `reranker_top_k` | `30` | Candidates fed to reranker |
| `max_hops` | `3` | BFS depth in graph search |
| `dedup_similarity_threshold` | `0.92` | Embedding cosine threshold for entity dedup |
| `dedup_fuzzy_threshold` | `0.85` | Fuzzy string threshold for entity dedup |
| `recency_decay_rate` | `0.02` | Exponential decay (half-life ~35 hours) |

---

## Development

```bash
git clone https://github.com/Kaboom2025/engram
cd engram
pip install -e ".[dev]"

# Run tests
pytest tests/unit/ -v

# Run with coverage
pytest --cov=engram --cov-report=term-missing

# Lint / format
python -m ruff check src/ tests/
python -m ruff format src/ tests/

# Run demo
python demo.py

# Ingest your code
python ingest_folder.py . --no-llm --compare "how does retrieval work?"

# Frontend (React + Vite)
cd web && npm install && npm run dev
```

---

## Roadmap

- [x] Embedded local mode (Kuzu + LanceDB + SQLite)
- [x] Hybrid retrieval (vector + graph + temporal)
- [x] Weighted RRF fusion with multi-source bonus
- [x] Query classification (temporal / factual / preference / global)
- [x] Global search (degree-centrality for overview queries)
- [x] Optional cross-encoder reranker
- [x] Gleaning (multi-pass LLM extraction)
- [x] Interactive graph visualization
- [x] Google Gemini multimodal embeddings (text + image + audio + video + PDF)
- [x] MCP server integration
- [x] LangChain + OpenAI Agents SDK integrations
- [x] React frontend with 8-panel interactive pipeline walkthrough
- [ ] Cloud mode (PostgreSQL + managed API)
- [ ] LongMemEval benchmark (target: >78% overall)
- [ ] Streaming ingestion

---

## License

MIT © 2025 Engram
