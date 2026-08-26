# Phase 1 / MVP Spec: Learned Memory Layer for AI Agents

**Codename:** (TBD — pick something short, `pip install`-able, and memorable)
**Author:** Saalik
**Date:** March 2026
**Target:** Solo founder, 3–6 month build, <$800/mo infra

---

## 1. Product Vision (One Paragraph)

An open-source memory layer for AI agents that combines a knowledge graph, vector search, and temporal awareness into a single hybrid retrieval system. Agents ingest conversations, documents, and signals; the system extracts structured facts and relationships, versions them over time, and retrieves the right context at query time using a weighted fusion of graph traversal, semantic similarity, and recency. Ships as a Python SDK (TypeScript later), a REST API, and a hosted cloud — competing on retrieval accuracy against Mem0 and developer experience against Zep/Graphiti.

**Phase 1 does NOT include:** per-customer learned traversal policies (Phase 2), LoRA adapters (Phase 3), or multi-region deployment. Phase 1 ships the architecture that makes those possible later.

---

## 2. What We're Building (Scope)

### In Scope (Phase 1)

| Component | Description |
|-----------|-------------|
| **Python SDK** | `pip install <name>`, 3-line integration, async-first |
| **Ingestion pipeline** | Conversations, documents, raw text → extracted entities, facts, relationships |
| **Knowledge graph** | Entity nodes + typed, timestamped edges with append-only versioning |
| **Vector index** | Embeddings over node summaries, not raw text chunks |
| **Hybrid retrieval** | Parallel fanout (graph + vector + temporal) → weighted RRF fusion → context assembly |
| **REST API** | CRUD for memories, search endpoint, tenant isolation |
| **Multi-tenancy** | User-level and org-level memory isolation |
| **LangChain/LangGraph integration** | `ChatMessageHistory` + retriever interface |
| **OpenAI Agents SDK integration** | Tool-based memory access |
| **MCP server** | For Claude Desktop / Cursor / Windsurf users |
| **Hosted cloud (basic)** | Single-region, usage-based pricing, free tier |
| **Eval harness** | LongMemEval-S runner + custom eval suite |
| **Docs site** | Quickstart, API reference, architecture guide |

### Out of Scope (Phase 1)

- Per-customer fine-tuned traversal models
- Multi-region / edge deployment
- TypeScript SDK (Python first, TS in Phase 2)
- GUI / dashboard (API + CLI only)
- Self-hosted enterprise installer
- SOC 2 / HIPAA compliance
- CrewAI / AutoGen integrations (community PRs welcome)

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Client SDKs                         │
│   Python SDK  │  REST API  │  MCP Server  │  LangChain  │
└──────┬────────┴─────┬──────┴──────┬───────┴──────┬──────┘
       │              │             │              │
       ▼              ▼             ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                           │
│         Auth (API keys) + Tenant Isolation               │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  Ingestion   │ │ Retrieval│ │   Memory     │
│  Pipeline    │ │ Engine   │ │   CRUD       │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                   Storage Layer                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐  │
│  │ Graph DB │  │ Vector DB │  │  Metadata / Relational│  │
│  │ (Kuzu)   │  │ (LanceDB) │  │  (PostgreSQL)        │  │
│  └──────────┘  └───────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Why These Storage Choices

| Store | Choice | Rationale |
|-------|--------|-----------|
| **Graph** | **Kuzu** (embedded) | Apache 2.0, embeddable (no separate server), fast Cypher-compatible queries, great for solo founder (zero ops). Swap to Neo4j for cloud scale later. |
| **Vector** | **LanceDB** (embedded) | Apache 2.0, Rust-core, zero-copy, used as default in Microsoft GraphRAG. Embeddable = no infra. |
| **Relational** | **PostgreSQL** | Tenants, users, API keys, billing metadata. The boring reliable choice. SQLite for local/dev mode. |
| **Embeddings** | **`all-MiniLM-L6-v2`** (local) or **`text-embedding-3-small`** (cloud) | Local model = zero cost for OSS users. Cloud model = better quality for hosted tier. 384-dim / 1536-dim respectively. |
| **LLM for extraction** | **`gpt-4.1-nano`** or **`claude-haiku`** | Cheapest capable models for entity/relationship extraction. Users can BYO API key. |

---

## 4. Data Model

### 4.1 Core Entities

```
┌─────────────────────────────────────────────────┐
│ Tenant                                           │
│  id: uuid                                        │
│  name: str                                       │
│  api_key_hash: str                               │
│  plan: enum(free, starter, pro)                  │
│  created_at: datetime                            │
└─────────────────────────────────────────────────┘
         │ has many
         ▼
┌─────────────────────────────────────────────────┐
│ User (end-user of the agent, not our customer)   │
│  id: uuid                                        │
│  tenant_id: uuid (FK)                            │
│  external_id: str (customer's user ID)           │
│  metadata: jsonb                                 │
│  created_at: datetime                            │
└─────────────────────────────────────────────────┘
         │ has many
         ▼
┌─────────────────────────────────────────────────┐
│ Session                                          │
│  id: uuid                                        │
│  user_id: uuid (FK)                              │
│  agent_id: str (optional, for multi-agent)       │
│  started_at: datetime                            │
│  last_active_at: datetime                        │
└─────────────────────────────────────────────────┘
```

### 4.2 Knowledge Graph Schema (in Kuzu)

```cypher
-- Nodes
CREATE NODE TABLE Entity (
    id STRING PRIMARY KEY,
    tenant_id STRING,
    user_id STRING,
    name STRING,
    entity_type STRING,        -- "person", "project", "tool", "preference", etc.
    summary STRING,            -- Natural language summary for embedding
    embedding FLOAT[384],      -- Duplicated in LanceDB for fast ANN
    confidence FLOAT,
    created_at TIMESTAMP,
    last_referenced_at TIMESTAMP,
    source_session_id STRING,
    metadata STRING            -- JSON blob
);

-- Edges (append-only, versioned)
CREATE REL TABLE Relationship (
    FROM Entity TO Entity,
    id STRING,
    rel_type STRING,           -- "decided", "prefers", "works_at", "replaced", etc.
    summary STRING,            -- "User decided to use FastAPI for the backend"
    confidence FLOAT,
    valid_from TIMESTAMP,      -- When this fact became true
    invalid_from TIMESTAMP,    -- When this fact was superseded (NULL = still active)
    source_session_id STRING,
    source_message_idx INT,    -- Index in conversation for traceability
    reasoning STRING,          -- WHY this edge was created (decision context)
    metadata STRING
);
```

**Key design decisions:**

1. **Append-only edges**: When a fact changes, we don't update the old edge. We set `invalid_from` on the old one and create a new edge with `valid_from = now()`. This gives us full temporal history — identical to HydraDB's "git-style" approach.

2. **Embeddings live in both Kuzu and LanceDB**: Kuzu stores them for graph-local operations; LanceDB stores them for fast ANN search. Sync is write-time (dual-write on ingest).

3. **Entity deduplication**: On ingest, we check if an entity with a similar name + type already exists (embedding similarity > 0.92). If so, we merge rather than create a duplicate.

### 4.3 Fact Types (Relationship Edge Types)

```python
class RelType(str, Enum):
    # High-signal edges (weighted heavily in retrieval)
    DECIDED = "decided"           # "User decided X"
    PREFERS = "prefers"           # "User prefers X over Y"
    BELIEVES = "believes"         # "User believes X"
    WORKS_ON = "works_on"         # "User is working on project X"
    REPLACED = "replaced"         # "X replaced Y" (temporal chain)

    # Medium-signal edges
    MENTIONED = "mentioned"       # "User mentioned X"
    ASKED_ABOUT = "asked_about"   # "User asked about X"
    RELATED_TO = "related_to"     # General association
    DEPENDS_ON = "depends_on"     # "X depends on Y"
    PART_OF = "part_of"           # "X is part of Y"

    # Meta edges
    CONTRADICTS = "contradicts"   # "X contradicts previous fact Y"
    SUPERSEDES = "supersedes"     # Explicit version chain
    DERIVED_FROM = "derived_from" # Provenance tracking
```

---

## 5. Ingestion Pipeline

### 5.1 Input Formats

```python
# The three ingestion entry points

# 1. Conversation messages (most common)
memory.add_messages(
    user_id="user_123",
    session_id="session_456",
    messages=[
        {"role": "user", "content": "Let's go with FastAPI for the backend"},
        {"role": "assistant", "content": "Great choice! I'll note that..."},
    ]
)

# 2. Raw text / documents
memory.add_document(
    user_id="user_123",
    content="Meeting notes: We decided to migrate from AWS to GCP...",
    metadata={"source": "meeting_notes", "date": "2026-03-20"}
)

# 3. Explicit facts (for programmatic ingestion)
memory.add_fact(
    user_id="user_123",
    subject="user",
    predicate="prefers",
    object="dark mode",
    confidence=0.95
)
```

### 5.2 Extraction Pipeline

```
Raw Input
    │
    ▼
┌──────────────┐
│ Preprocessor │  Chunk long docs, deduplicate, normalize
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Entity Extractor │  LLM call: extract entities + types
│ (gpt-4.1-nano)  │  Structured output → list of entities
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Relation Extract │  LLM call: extract relationships between entities
│ (gpt-4.1-nano)  │  Structured output → list of (subj, pred, obj, context)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Entity Resolver  │  Deduplicate: "FastAPI" == "fast api" == "Fast API"
│ (embedding sim)  │  Merge into existing graph nodes if match > 0.92
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Temporal Linker  │  Check for contradictions with existing facts
│                  │  If conflict: set invalid_from on old edge, create new
│                  │  If new: create fresh edge with valid_from = now()
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Dual Writer      │  Write nodes/edges to Kuzu
│                  │  Write embeddings to LanceDB
│                  │  Write metadata to PostgreSQL
└──────────────────┘
```

### 5.3 Extraction Prompt (Core)

```python
EXTRACTION_SYSTEM_PROMPT = """You are a memory extraction system. Given a conversation
or document, extract structured facts as JSON.

For each fact, extract:
- subject: the entity performing/holding the fact
- subject_type: person | project | tool | concept | preference | organization
- predicate: the relationship type (decided, prefers, works_on, mentioned, etc.)
- object: the target entity
- object_type: same types as subject_type
- confidence: 0.0-1.0 how confident you are this is a real fact
- is_update: true if this contradicts or updates a previously known fact
- reasoning: brief explanation of why this fact matters

Rules:
- Extract ONLY facts that would be useful to recall in future conversations
- Preferences > decisions > mentions (prioritize high-signal facts)
- If user corrects themselves, mark is_update=true
- Do NOT extract pleasantries, filler, or meta-conversation
- Output ONLY valid JSON array, no markdown, no preamble

Example output:
[
  {
    "subject": "user",
    "subject_type": "person",
    "predicate": "decided",
    "object": "FastAPI",
    "object_type": "tool",
    "confidence": 0.95,
    "is_update": false,
    "reasoning": "User explicitly stated their tech stack choice"
  }
]"""
```

### 5.4 Ingestion Cost Estimate

| Input | LLM calls | Est. cost per 1K messages |
|-------|-----------|--------------------------|
| Entity extraction | 1 per message batch (5-10 msgs) | ~$0.003 |
| Relation extraction | 1 per message batch | ~$0.003 |
| Embedding generation | 1 per entity (local model = free) | $0.00 (local) / $0.001 (cloud) |
| **Total** | | **~$0.006 – $0.01 per 1K messages** |

---

## 6. Retrieval Engine (The Hybrid Layer)

This is the core differentiator. Phase 1 uses hand-tuned heuristics; Phase 2 replaces them with a learned router.

### 6.1 Query Flow

```python
async def search(
    query: str,
    user_id: str,
    session_id: str | None = None,
    top_k: int = 10,
    token_budget: int = 4000,
) -> MemoryContext:
    # Step 1: Classify query to set weights
    weights = classify_query(query)

    # Step 2: Parallel retrieval fanout
    vector_results, graph_results, temporal_results = await asyncio.gather(
        vector_search(query, user_id, top_k=50),
        graph_search(query, user_id, max_hops=3),
        temporal_search(query, user_id, session_id),
    )

    # Step 3: Weighted RRF fusion
    fused = fuse_candidates(
        vector_results, graph_results, temporal_results, weights
    )

    # Step 4: Conflict resolution (latest version wins)
    resolved = resolve_temporal_conflicts(fused)

    # Step 5: Context assembly (pack into token budget)
    context = assemble_context(resolved, token_budget)

    return context
```

### 6.2 Query Classification (Heuristic, Phase 1)

```python
def classify_query(query: str) -> RetrievalWeights:
    """Rule-based query classification. Phase 2 replaces with learned router."""
    q = query.lower()

    # Temporal queries: boost temporal weight
    temporal_signals = ["when", "last time", "recently", "before", "after",
                        "yesterday", "last week", "first time", "history"]
    if any(signal in q for signal in temporal_signals):
        return RetrievalWeights(vector=0.20, graph=0.30, temporal=0.50)

    # Factual lookups: boost graph weight
    factual_signals = ["what is", "who is", "where does", "email", "name",
                       "address", "phone", "role", "title"]
    if any(signal in q for signal in factual_signals):
        return RetrievalWeights(vector=0.20, graph=0.60, temporal=0.20)

    # Preference / opinion queries: boost vector weight
    pref_signals = ["prefer", "like", "favorite", "opinion", "think about",
                    "feel about", "style", "approach"]
    if any(signal in q for signal in pref_signals):
        return RetrievalWeights(vector=0.50, graph=0.30, temporal=0.20)

    # Default balanced
    return RetrievalWeights(vector=0.35, graph=0.40, temporal=0.25)
```

### 6.3 Vector Search

```python
async def vector_search(query: str, user_id: str, top_k: int = 50):
    query_embedding = embed(query)
    # Search over entity node summaries, NOT raw text chunks
    results = lancedb_table.search(query_embedding)
        .where(f"user_id = '{user_id}'")
        .limit(top_k)
        .to_list()
    return [
        ScoredNode(node_id=r["id"], score=r["_distance"], source="vector")
        for r in results
    ]
```

### 6.4 Graph Search

```python
async def graph_search(query: str, user_id: str, max_hops: int = 3):
    # Extract entities from query
    entities = extract_query_entities(query)  # lightweight NER or LLM

    # Find anchor nodes via fuzzy match + embedding similarity
    anchors = []
    for entity in entities:
        matches = kuzu.execute("""
            MATCH (e:Entity)
            WHERE e.user_id = $user_id
              AND (e.name CONTAINS $entity OR e.entity_type = $entity)
            RETURN e
            ORDER BY e.last_referenced_at DESC
            LIMIT 5
        """, {"user_id": user_id, "entity": entity})
        anchors.extend(matches)

    # BFS traversal with edge-type weighting
    EDGE_WEIGHTS = {
        "decided": 1.0, "prefers": 0.95, "replaced": 0.9,
        "works_on": 0.85, "depends_on": 0.8, "believes": 0.8,
        "part_of": 0.7, "related_to": 0.5, "mentioned": 0.3,
        "asked_about": 0.2,
    }

    visited = set()
    candidates = []

    for anchor in anchors:
        queue = [(anchor, 0, 1.0)]  # (node, depth, accumulated_weight)
        while queue:
            node, depth, weight = queue.pop(0)
            if node.id in visited or depth > max_hops:
                continue
            visited.add(node.id)

            candidates.append(ScoredNode(
                node_id=node.id,
                score=weight * (0.7 ** depth),  # decay per hop
                source="graph"
            ))

            # Get outgoing edges (active only)
            edges = kuzu.execute("""
                MATCH (a:Entity)-[r:Relationship]->(b:Entity)
                WHERE a.id = $node_id AND r.invalid_from IS NULL
                RETURN r, b
            """, {"node_id": node.id})

            for edge, neighbor in edges:
                edge_weight = EDGE_WEIGHTS.get(edge.rel_type, 0.3)
                queue.append((neighbor, depth + 1, weight * edge_weight))

    return candidates
```

### 6.5 Temporal Search

```python
async def temporal_search(
    query: str, user_id: str, session_id: str | None
):
    candidates = []

    # 1. Current session facts (highest recency boost)
    if session_id:
        session_facts = kuzu.execute("""
            MATCH (e:Entity)-[r:Relationship]->()
            WHERE e.user_id = $user_id
              AND r.source_session_id = $session_id
              AND r.invalid_from IS NULL
            RETURN e, r
            ORDER BY r.valid_from DESC
        """, {"user_id": user_id, "session_id": session_id})
        for entity, rel in session_facts:
            candidates.append(ScoredNode(
                node_id=entity.id, score=1.0, source="temporal"
            ))

    # 2. Recent facts (last 7 days, decaying)
    recent_facts = kuzu.execute("""
        MATCH (e:Entity)-[r:Relationship]->()
        WHERE e.user_id = $user_id
          AND r.valid_from > $cutoff
          AND r.invalid_from IS NULL
        RETURN e, r
        ORDER BY r.valid_from DESC
        LIMIT 100
    """, {"user_id": user_id, "cutoff": now() - timedelta(days=7)})

    for entity, rel in recent_facts:
        age_hours = (now() - rel.valid_from).total_seconds() / 3600
        decay = math.exp(-0.02 * age_hours)  # half-life ~35 hours
        candidates.append(ScoredNode(
            node_id=entity.id, score=decay, source="temporal"
        ))

    # 3. Recently referenced (even if old, user brought it up recently)
    referenced = kuzu.execute("""
        MATCH (e:Entity)
        WHERE e.user_id = $user_id
          AND e.last_referenced_at > $cutoff
        RETURN e
        ORDER BY e.last_referenced_at DESC
        LIMIT 50
    """, {"user_id": user_id, "cutoff": now() - timedelta(days=3)})

    for entity in referenced:
        candidates.append(ScoredNode(
            node_id=entity.id, score=0.6, source="temporal"
        ))

    return candidates
```

### 6.6 Fusion (Weighted RRF)

```python
def fuse_candidates(
    vector_results: list[ScoredNode],
    graph_results: list[ScoredNode],
    temporal_results: list[ScoredNode],
    weights: RetrievalWeights,
    k: int = 60,  # RRF constant
) -> list[ScoredNode]:
    scores: dict[str, FusionScore] = defaultdict(
        lambda: FusionScore(vector=0, graph=0, temporal=0, sources=0)
    )

    for rank, node in enumerate(sorted(vector_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].vector = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    for rank, node in enumerate(sorted(graph_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].graph = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    for rank, node in enumerate(sorted(temporal_results, key=lambda n: n.score, reverse=True)):
        scores[node.node_id].temporal = 1.0 / (k + rank)
        scores[node.node_id].sources += 1

    final = []
    for node_id, s in scores.items():
        combined = (
            weights.vector * s.vector
            + weights.graph * s.graph
            + weights.temporal * s.temporal
        )
        # Multi-source bonus: appearing in 2+ retrieval paths = strong signal
        if s.sources >= 2:
            combined *= 1.0 + (0.15 * (s.sources - 1))

        final.append((node_id, combined))

    final.sort(key=lambda x: x[1], reverse=True)
    return final
```

### 6.7 Context Assembly

```python
def assemble_context(
    ranked_nodes: list[tuple[str, float]],
    token_budget: int = 4000,
) -> MemoryContext:
    blocks = []
    tokens_used = 0

    for node_id, score in ranked_nodes:
        node = get_node(node_id)
        edges = get_active_edges(node_id)

        # Format: "FastAPI (tool): User decided to use for backend (2026-03-01).
        #          Replaced Django. Depends on Uvicorn."
        block = format_node_with_edges(node, edges)
        block_tokens = count_tokens(block)

        if tokens_used + block_tokens > token_budget:
            break

        blocks.append(ContextBlock(
            content=block,
            node_id=node_id,
            score=score,
            timestamp=node.created_at,
        ))
        tokens_used += block_tokens

    return MemoryContext(
        blocks=blocks,
        total_tokens=tokens_used,
        retrieval_metadata={
            "candidates_considered": len(ranked_nodes),
            "blocks_returned": len(blocks),
        }
    )
```

---

## 7. SDK Design

### 7.1 Core API (Python)

```python
from <name> import MemoryClient

# Initialize
memory = MemoryClient(
    api_key="sk-...",          # For hosted cloud
    # OR
    local=True,                # For embedded/self-hosted mode
    storage_path="./memory_data",
)

# ── Ingest ──────────────────────────────────────────────

# Add conversation messages
memory.add(
    messages=[
        {"role": "user", "content": "I'm switching from Django to FastAPI"},
        {"role": "assistant", "content": "Got it, I'll remember that."},
    ],
    user_id="user_123",
    session_id="sess_abc",
)

# Add a document
memory.add(
    text="Q1 OKR: Migrate 80% of services to Kubernetes by March.",
    user_id="user_123",
    metadata={"source": "okr_doc", "quarter": "Q1"},
)

# ── Retrieve ────────────────────────────────────────────

# Search memories
results = memory.search(
    query="What backend framework are we using?",
    user_id="user_123",
    top_k=10,
    token_budget=4000,  # Optional: pack results into token limit
)

# Returns:
# MemoryContext(
#   text="User decided to use FastAPI for the backend (Mar 1, 2026)...",
#   facts=[Fact(subject="user", predicate="decided", object="FastAPI", ...)],
#   tokens_used=312,
# )

# Use in a prompt
response = openai.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": f"User context:\n{results.text}"},
        {"role": "user", "content": user_message},
    ],
)

# ── Manage ──────────────────────────────────────────────

# Get all memories for a user
all_memories = memory.get_all(user_id="user_123")

# Get memory history (temporal chain)
history = memory.history(
    user_id="user_123",
    entity="backend_framework",
)
# Returns: [("Django", valid_from=Jan, invalid_from=Mar),
#           ("FastAPI", valid_from=Mar, invalid_from=None)]

# Delete a specific memory
memory.delete(memory_id="mem_xyz")

# Delete all memories for a user (GDPR)
memory.delete_user(user_id="user_123")
```

### 7.2 LangChain Integration

```python
from <name>.integrations.langchain import MemoryRetriever, MemoryChatHistory

# As a retriever
retriever = MemoryRetriever(
    client=memory,
    user_id="user_123",
    top_k=10,
)

# As chat message history
history = MemoryChatHistory(
    client=memory,
    user_id="user_123",
    session_id="sess_abc",
)
```

### 7.3 OpenAI Agents SDK Integration

```python
from <name>.integrations.openai import memory_tools

# Returns a list of Tool objects: search_memory, add_memory, get_history
tools = memory_tools(client=memory, user_id="user_123")

agent = Agent(
    name="assistant",
    instructions="You have access to memory tools...",
    tools=tools,
)
```

### 7.4 MCP Server

```bash
# Run as MCP server for Claude Desktop / Cursor
<name> serve --mcp --port 8765
```

Exposes tools: `memory_search`, `memory_add`, `memory_history`, `memory_delete`.

---

## 8. REST API

### Endpoints

```
POST   /v1/memories              # Add messages/documents/facts
GET    /v1/memories/search       # Hybrid retrieval
GET    /v1/memories              # List all memories for a user
GET    /v1/memories/:id          # Get specific memory
DELETE /v1/memories/:id          # Delete specific memory
GET    /v1/memories/history      # Temporal chain for an entity
DELETE /v1/users/:id/memories    # Delete all memories for a user (GDPR)
GET    /v1/health                # Health check
```

### Auth

- API key in `Authorization: Bearer sk-...` header
- Tenant isolation enforced at query level (every query scoped to tenant)
- User isolation enforced by `user_id` parameter

### Search Request/Response

```json
// POST /v1/memories/search
{
  "query": "What backend framework are we using?",
  "user_id": "user_123",
  "session_id": "sess_abc",       // optional
  "top_k": 10,                    // optional, default 10
  "token_budget": 4000,           // optional
  "filters": {                    // optional
    "entity_types": ["tool", "decision"],
    "after": "2026-01-01T00:00:00Z"
  }
}

// Response
{
  "context": "User decided to use FastAPI for the backend (2026-03-01)...",
  "facts": [
    {
      "id": "fact_abc123",
      "subject": "user",
      "predicate": "decided",
      "object": "FastAPI",
      "object_type": "tool",
      "valid_from": "2026-03-01T10:30:00Z",
      "confidence": 0.95,
      "source_session": "sess_xyz"
    }
  ],
  "metadata": {
    "tokens_used": 312,
    "candidates_considered": 47,
    "retrieval_ms": 83,
    "sources": {"vector": 12, "graph": 8, "temporal": 5}
  }
}
```

---

## 9. Infrastructure & Deployment

### Local / Open-Source Mode

```
┌──────────────────────────────────┐
│  Single Process (Python)          │
│  ┌─────────┐  ┌─────────┐       │
│  │ Kuzu    │  │ LanceDB │       │
│  │ (embed) │  │ (embed) │       │
│  └─────────┘  └─────────┘       │
│  ┌────────────────────────┐      │
│  │ SQLite (metadata)      │      │
│  └────────────────────────┘      │
│  ┌────────────────────────┐      │
│  │ sentence-transformers  │      │
│  │ (local embeddings)     │      │
│  └────────────────────────┘      │
└──────────────────────────────────┘

pip install <name>
# That's it. No Docker, no external services.
```

### Hosted Cloud Mode

```
┌──────────────────────────────────────────────┐
│  Railway / Fly.io / Render                    │
│                                               │
│  FastAPI app (2 replicas)                     │
│  ├── Kuzu (embedded per replica, or shared)   │
│  ├── LanceDB (object storage backend)         │
│  └── PostgreSQL (managed, e.g. Neon / Supabase)│
└──────────────────────────────────────────────┘
```

### Cost Estimate (Hosted, Month 1-6)

| Item | Cost/mo |
|------|---------|
| App hosting (Railway/Fly, 2 instances) | $40-100 |
| PostgreSQL (Neon free tier → Supabase) | $0-25 |
| Object storage (LanceDB data on S3/R2) | $5-20 |
| LLM API costs (extraction, at low volume) | $20-100 |
| Domain + DNS | $15 |
| Monitoring (Sentry free tier) | $0 |
| **Total** | **$80-260** |

---

## 10. Eval & Benchmarks

### 10.1 LongMemEval-S Runner

Build a harness that runs the LongMemEval-S benchmark (500 questions, ~115K token contexts) against our system. Target scores:

| Category | Target (Phase 1) | Mem0 baseline | Zep baseline |
|----------|-------------------|---------------|--------------|
| Single-session extraction | >95% | ~85% | ~94% |
| Multi-session reasoning | >75% | ~60% | ~80% |
| Temporal reasoning | >70% | ~50% | ~75% |
| Knowledge updates | >80% | ~65% | ~85% |
| Abstention | >70% | ~55% | ~70% |
| **Overall** | **>78%** | **~65%** | **~82%** |

### 10.2 Custom Eval Suite

```python
# tests/eval/test_retrieval.py
def test_fact_update_retrieval():
    """When a fact is updated, only the latest version should be returned."""
    memory.add(messages=[...])  # "I work at Google"
    memory.add(messages=[...])  # "I just moved to Microsoft"
    result = memory.search("Where do I work?", user_id="test")
    assert "Microsoft" in result.text
    assert "Google" not in result.text  # Old fact should be filtered

def test_multi_hop_retrieval():
    """Graph traversal should connect entities across hops."""
    memory.add(messages=[...])  # "Project Alpha uses FastAPI"
    memory.add(messages=[...])  # "FastAPI depends on Uvicorn"
    result = memory.search("What does Project Alpha depend on?", user_id="test")
    assert "Uvicorn" in result.text  # 2-hop: Alpha → FastAPI → Uvicorn

def test_temporal_decay():
    """Recent facts should score higher than old facts."""
    # ... add old and new facts, verify ranking

def test_entity_deduplication():
    """'FastAPI' and 'fast api' should resolve to the same entity."""
    # ...

def test_gdpr_deletion():
    """delete_user should remove ALL data across all stores."""
    # ...
```

---

## 11. Timeline

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1-2 | **Core data model + storage** | Kuzu schema, LanceDB integration, dual-write, basic CRUD |
| 3-4 | **Ingestion pipeline** | LLM extraction, entity resolution, temporal linking |
| 5-6 | **Hybrid retrieval engine** | Vector search, graph traversal, temporal search, RRF fusion |
| 7-8 | **Python SDK + REST API** | `pip install`-able package, FastAPI server, auth |
| 9-10 | **Integrations** | LangChain retriever, OpenAI Agents tools, MCP server |
| 11-12 | **Cloud deployment + eval** | Hosted tier on Railway/Fly, LongMemEval harness, docs site |
| 13-14 | **Beta launch** | Hacker News post, Discord, first 50 users |
| 15-16 | **Iterate on feedback** | Bug fixes, perf tuning, second batch of users |

**Milestone gates:**
- Week 6: Internal demo — can add conversations and retrieve correct context
- Week 10: External alpha — 5-10 trusted users testing integrations
- Week 14: Public beta — HN launch, open GitHub repo

---

## 12. Success Metrics (First 90 Days Post-Launch)

| Metric | Target |
|--------|--------|
| GitHub stars | 500+ |
| PyPI installs | 1,000+ |
| Cloud sign-ups (free tier) | 200+ |
| Paying customers | 5-10 |
| LongMemEval-S score | >78% overall |
| p95 retrieval latency | <200ms |
| Ingestion throughput | >100 messages/sec |

---

## 13. What Phase 2 Adds (Preview)

Once Phase 1 is stable and generating revenue:

1. **Learned query router**: Replace the heuristic `classify_query()` with a fine-tuned T5-Large that learns optimal retrieval weights from user interaction data
2. **Adaptive edge weights**: Replace static `EDGE_WEIGHTS` dict with weights learned from retrieval success/failure signals
3. **TypeScript SDK**: Same API surface, for Node.js agent builders
4. **Dashboard**: Web UI for visualizing the knowledge graph, debugging retrieval, monitoring usage
5. **Self-RAG loop**: When retrieval confidence is low, automatically refine the query and retry with different weights

---

## 14. Open Questions / Decisions Needed

1. **Name**: Needs to be short, memorable, available on PyPI/npm, and have an available .com or .dev domain
2. **License**: MIT (maximum adoption) vs Apache 2.0 (patent protection) vs BSL (Zep's approach, restricts hosted competitors)
3. **Local LLM option**: Should we support Ollama for fully offline extraction? Adds complexity but appeals to privacy-conscious users
4. **Graph DB for cloud**: Kuzu embedded works for local + small cloud, but at scale we'd want Neo4j or FalkorDB. When to make that transition?
5. **Pricing model**: Per-memory-stored (Mem0 style) vs per-retrieval-call vs per-ingestion-episode (Zep style)?
