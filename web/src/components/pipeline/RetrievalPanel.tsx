import { memo } from 'react'
import { motion } from 'framer-motion'
import {
  VECTOR_RESULTS,
  GRAPH_RESULTS,
  TEMPORAL_RESULTS,
  FUSED_RESULTS,
  type ScoredResult,
  type FusedResult,
} from '../../data/pipelineData'

const LANE_CONFIG = {
  vector: { label: 'Vector Search', color: 'text-accent', border: 'border-accent/30', bg: 'bg-accent/5', results: VECTOR_RESULTS },
  graph: { label: 'Graph Search', color: 'text-green', border: 'border-green/30', bg: 'bg-green/5', results: GRAPH_RESULTS },
  temporal: { label: 'Temporal Search', color: 'text-orange', border: 'border-orange/30', bg: 'bg-orange/5', results: TEMPORAL_RESULTS },
}

const SOURCE_COLOR: Record<string, string> = {
  vector: 'text-accent',
  graph: 'text-green',
  temporal: 'text-orange',
}

function ResultCard({ result }: { result: ScoredResult }) {
  return (
    <div className="flex items-center justify-between text-xs py-1.5 border-b border-border/40 last:border-0">
      <span className="text-gray-300 font-medium">{result.entityName}</span>
      <div className="flex items-center gap-2">
        <span className="text-gray-600 font-mono">{result.detail}</span>
        <span className="font-mono font-semibold text-white">{result.score.toFixed(2)}</span>
      </div>
    </div>
  )
}

function Lane({ laneKey, delay }: { laneKey: keyof typeof LANE_CONFIG; delay: number }) {
  const { label, color, border, bg, results } = LANE_CONFIG[laneKey]
  return (
    <motion.div
      className={`rounded-xl border ${border} ${bg} p-4 space-y-3 flex-1 min-w-0`}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.1 }}
      transition={{ duration: 0.45, delay }}
    >
      <p className={`text-xs font-semibold uppercase tracking-wider ${color}`}>{label}</p>
      <div>
        {results.map((r, i) => (
          <ResultCard key={i} result={r} />
        ))}
      </div>
    </motion.div>
  )
}

function FusedCard({ result, rank }: { result: FusedResult; rank: number }) {
  const stars = result.hasBonus ? (result.sources.length === 3 ? '★★★' : '★★') : ''
  return (
    <motion.div
      className="flex items-center justify-between py-2 border-b border-border/40 last:border-0"
      initial={{ opacity: 0, x: -8 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.8 + rank * 0.08 }}
    >
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-600 font-mono w-4">{rank + 1}.</span>
        <span className="text-sm text-white font-medium">{result.entityName}</span>
        {stars && <span className="text-xs text-yellow-400">{stars}</span>}
      </div>
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          {result.sources.map(s => (
            <span key={s} className={`text-xs font-mono ${SOURCE_COLOR[s] ?? 'text-gray-400'}`}>
              {s[0].toUpperCase()}
            </span>
          ))}
        </div>
        <span className="text-xs font-mono font-semibold text-white">{result.score.toFixed(4)}</span>
      </div>
    </motion.div>
  )
}

export const RetrievalPanel = memo(function RetrievalPanel() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4">
        {(Object.keys(LANE_CONFIG) as Array<keyof typeof LANE_CONFIG>).map((key, i) => (
          <Lane key={key} laneKey={key} delay={i * 0.15} />
        ))}
      </div>

      <motion.div
        className="flex items-center gap-3 text-gray-600 text-xs"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.6 }}
      >
        <div className="h-px flex-1 bg-border" />
        <span>Weighted Reciprocal Rank Fusion (RRF)</span>
        <div className="h-px flex-1 bg-border" />
      </motion.div>

      <motion.div
        className="rounded-xl bg-surface-2 border border-border p-4"
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.7 }}
      >
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Fused Results</p>
        {FUSED_RESULTS.map((r, i) => (
          <FusedCard key={r.entityName} result={r} rank={i} />
        ))}
        <p className="text-xs text-gray-600 mt-3">
          ★★★ = all 3 sources (1.30× bonus) · ★★ = 2 sources (1.15× bonus) · V/G/T = vector/graph/temporal
        </p>
      </motion.div>
    </div>
  )
})
