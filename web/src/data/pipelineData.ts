export interface ExtractedFact {
  subject: string
  subjectType: string
  predicate: string
  object: string
  objectType: string
  confidence: number
  gleanRound: 0 | 1
}

export interface MergeCandidate {
  variants: string[]
  canonical: string
  fuzzyScore: number
  embeddingScore: number
}

export interface TemporalFact {
  subject: string
  predicate: string
  object: string
  validFrom: string
  invalidFrom: string | null
  isActive: boolean
  conflictNote?: string
}

export interface GraphNode {
  id: string
  label: string
  type: 'person' | 'tool' | 'concept' | 'project'
  x: number
  y: number
  size: number
}

export interface GraphEdge {
  from: string
  to: string
  label: string
  weight: number
  active: boolean
}

export interface ScoredResult {
  entityName: string
  score: number
  source: 'vector' | 'graph' | 'temporal'
  detail: string
}

export interface FusedResult {
  entityName: string
  score: number
  sources: string[]
  hasBonus: boolean
}

export interface SourceBlock {
  text: string
  source: 'vector' | 'graph' | 'temporal' | 'graph+temporal'
}

// Panel 1 — Raw Conversation
export const CONVERSATION_LINES = [
  { speaker: 'Saalik', text: "We've been using Django but I've decided to switch to FastAPI." },
  { speaker: 'Saalik', text: "It's faster and the async support is native." },
  { speaker: 'Alex', text: "What about the ORM? Django has great ORM support." },
  { speaker: 'Saalik', text: "We'll use SQLAlchemy with FastAPI. Already depends on Pydantic" },
  { speaker: 'Saalik', text: "which FastAPI uses natively." },
]

export const ENTITY_COLOR_MAP: Record<string, string> = {
  Saalik: 'text-orange',
  Alex: 'text-orange',
  Django: 'text-accent',
  FastAPI: 'text-accent',
  SQLAlchemy: 'text-accent',
  Pydantic: 'text-green',
}

// Panel 2 — Extracted Facts
export const EXTRACTED_FACTS: ExtractedFact[] = [
  { subject: 'Saalik', subjectType: 'person', predicate: 'decided', object: 'FastAPI', objectType: 'tool', confidence: 0.95, gleanRound: 0 },
  { subject: 'Saalik', subjectType: 'person', predicate: 'replaced', object: 'Django', objectType: 'tool', confidence: 0.95, gleanRound: 0 },
  { subject: 'FastAPI', subjectType: 'tool', predicate: 'depends_on', object: 'Pydantic', objectType: 'concept', confidence: 0.90, gleanRound: 0 },
  { subject: 'Saalik', subjectType: 'person', predicate: 'will_use', object: 'SQLAlchemy', objectType: 'tool', confidence: 0.88, gleanRound: 0 },
  { subject: 'FastAPI', subjectType: 'tool', predicate: 'has_feature', object: 'native async', objectType: 'concept', confidence: 0.85, gleanRound: 0 },
  { subject: 'Django', subjectType: 'tool', predicate: 'has_feature', object: 'ORM support', objectType: 'concept', confidence: 0.82, gleanRound: 0 },
  { subject: 'SQLAlchemy', subjectType: 'tool', predicate: 'related_to', object: 'Django ORM', objectType: 'concept', confidence: 0.80, gleanRound: 1 },
  { subject: 'FastAPI', subjectType: 'tool', predicate: 'part_of', object: 'Python async ecosystem', objectType: 'concept', confidence: 0.75, gleanRound: 1 },
  { subject: 'Alex', subjectType: 'person', predicate: 'concerned_about', object: 'ORM migration', objectType: 'concept', confidence: 0.70, gleanRound: 1 },
]

// Panel 3 — Entity Resolution
export const MERGE_CANDIDATES: MergeCandidate[] = [
  { variants: ['fastapi', 'FastAPI', 'fast-api'], canonical: 'FastAPI', fuzzyScore: 0.92, embeddingScore: 0.94 },
  { variants: ['Saalik', 'saalik'], canonical: 'Saalik', fuzzyScore: 0.86, embeddingScore: 0.97 },
]

// Panel 4 — Temporal Linking
export const TEMPORAL_FACTS: TemporalFact[] = [
  { subject: 'Saalik', predicate: 'decided', object: 'Django', validFrom: 'Mar 1, 2025', invalidFrom: 'Mar 15, 2025', isActive: false },
  { subject: 'Saalik', predicate: 'decided', object: 'FastAPI', validFrom: 'Mar 15, 2025', invalidFrom: null, isActive: true, conflictNote: 'Conflict detected — supersedes previous decision' },
]

// Panel 5 — Knowledge Graph (pre-calculated SVG positions, viewBox 700×420)
export const GRAPH_NODES: GraphNode[] = [
  { id: 'saalik', label: 'Saalik', type: 'person', x: 290, y: 200, size: 20 },
  { id: 'fastapi', label: 'FastAPI', type: 'tool', x: 480, y: 120, size: 18 },
  { id: 'django', label: 'Django', type: 'tool', x: 110, y: 290, size: 14 },
  { id: 'pydantic', label: 'Pydantic', type: 'concept', x: 590, y: 250, size: 14 },
  { id: 'sqlalchemy', label: 'SQLAlchemy', type: 'tool', x: 380, y: 360, size: 12 },
  { id: 'alex', label: 'Alex', type: 'person', x: 80, y: 150, size: 12 },
  { id: 'native_async', label: 'native async', type: 'concept', x: 590, y: 60, size: 10 },
  { id: 'orm', label: 'ORM support', type: 'concept', x: 150, y: 400, size: 10 },
]

export const GRAPH_EDGES: GraphEdge[] = [
  { from: 'saalik', to: 'fastapi', label: 'decided', weight: 1.0, active: true },
  { from: 'saalik', to: 'django', label: 'replaced', weight: 1.0, active: false },
  { from: 'fastapi', to: 'pydantic', label: 'depends_on', weight: 0.8, active: true },
  { from: 'saalik', to: 'sqlalchemy', label: 'will_use', weight: 0.8, active: true },
  { from: 'fastapi', to: 'native_async', label: 'has_feature', weight: 0.6, active: true },
  { from: 'django', to: 'orm', label: 'has_feature', weight: 0.6, active: true },
  { from: 'alex', to: 'django', label: 'mentioned', weight: 0.3, active: true },
  { from: 'sqlalchemy', to: 'orm', label: 'related_to', weight: 0.4, active: true },
]

// Panel 6 — Query Classification
export const CLASSIFICATION_EXAMPLES = [
  {
    query: 'What backend framework are we using?',
    type: 'FACTUAL',
    weights: { vector: 0.20, graph: 0.60, temporal: 0.20 },
    explanation: 'Factual queries emphasize graph structure — relationships like [decided] carry more signal than vector similarity.',
  },
  {
    query: 'When did we switch frameworks?',
    type: 'TEMPORAL',
    weights: { vector: 0.20, graph: 0.30, temporal: 0.50 },
    explanation: 'Temporal queries boost the recency layer — when an event happened matters most.',
  },
]

// Panel 7 — Retrieval Fanout
export const VECTOR_RESULTS: ScoredResult[] = [
  { entityName: 'FastAPI', score: 0.89, source: 'vector', detail: 'cosine: 0.89' },
  { entityName: 'Django', score: 0.75, source: 'vector', detail: 'cosine: 0.75' },
  { entityName: 'Pydantic', score: 0.72, source: 'vector', detail: 'cosine: 0.72' },
  { entityName: 'SQLAlchemy', score: 0.68, source: 'vector', detail: 'cosine: 0.68' },
  { entityName: 'Python', score: 0.55, source: 'vector', detail: 'cosine: 0.55' },
]

export const GRAPH_RESULTS: ScoredResult[] = [
  { entityName: 'FastAPI', score: 1.00, source: 'graph', detail: 'hop 0, anchor' },
  { entityName: 'Pydantic', score: 0.85, source: 'graph', detail: 'hop 1, depends_on' },
  { entityName: 'Saalik', score: 0.60, source: 'graph', detail: 'hop 1, decided' },
  { entityName: 'Django', score: 0.63, source: 'graph', detail: 'hop 1, replaced↓' },
  { entityName: 'SQLAlchemy', score: 0.42, source: 'graph', detail: 'hop 2' },
]

export const TEMPORAL_RESULTS: ScoredResult[] = [
  { entityName: 'FastAPI', score: 0.98, source: 'temporal', detail: 'recent, session fact' },
  { entityName: 'Saalik', score: 0.95, source: 'temporal', detail: 'referenced today' },
  { entityName: 'Django', score: 0.70, source: 'temporal', detail: 'invalidated, decay↓' },
  { entityName: 'SQLAlchemy', score: 0.60, source: 'temporal', detail: 'session mention' },
  { entityName: 'Pydantic', score: 0.55, source: 'temporal', detail: 'indirect reference' },
]

export const FUSED_RESULTS: FusedResult[] = [
  { entityName: 'FastAPI', score: 0.0187, sources: ['vector', 'graph', 'temporal'], hasBonus: true },
  { entityName: 'Pydantic', score: 0.0142, sources: ['vector', 'graph'], hasBonus: true },
  { entityName: 'Saalik', score: 0.0128, sources: ['graph', 'temporal'], hasBonus: true },
  { entityName: 'Django', score: 0.0098, sources: ['vector', 'graph', 'temporal'], hasBonus: false },
  { entityName: 'SQLAlchemy', score: 0.0085, sources: ['vector', 'graph', 'temporal'], hasBonus: false },
]

// Panel 8 — Assembled Context
export const ASSEMBLED_CONTEXT: SourceBlock[] = [
  { text: 'FastAPI is the backend framework.', source: 'graph' },
  { text: 'Saalik decided to use FastAPI, replacing Django.', source: 'graph+temporal' },
  { text: 'FastAPI depends on Pydantic for data validation.', source: 'vector' },
  { text: 'The switch happened on March 15, 2025.', source: 'temporal' },
  { text: 'SQLAlchemy will be used as the ORM layer.', source: 'graph' },
  { text: 'FastAPI provides native async support.', source: 'vector' },
]

export const RETRIEVAL_METADATA = {
  tokens: 847,
  retrieval: 47,
  blocks: 6,
  multiSource: 3,
}
