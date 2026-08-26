export interface GraphNode {
  id: string
  name: string
  entity_type: string
  summary: string
  confidence: number
}

export interface GraphEdge {
  from_id: string
  to_id: string
  rel_type: string
  summary: string
  confidence: number
  active: boolean
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface ScoreBreakdown {
  vector: number
  graph: number
  temporal: number
}

export interface SearchResult {
  context: string
  facts: Record<string, unknown>[]
  scores: ScoreBreakdown
  weights: ScoreBreakdown
  retrieval_ms: number
  source_counts: Record<string, number>
}

export interface ComparisonResult {
  engram: SearchResult
  naive: SearchResult
}

export interface Scenario {
  fact_count: number
  description: string
}
