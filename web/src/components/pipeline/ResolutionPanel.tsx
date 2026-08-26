import { memo } from 'react'
import { motion } from 'framer-motion'
import { MERGE_CANDIDATES, type MergeCandidate } from '../../data/pipelineData'

const FUZZY_THRESHOLD = 0.85
const EMBEDDING_THRESHOLD = 0.92

function ScoreBadge({ label, value, threshold }: { label: string; value: number; threshold: number }) {
  const passes = value >= threshold
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-gray-500">{label}</span>
      <span className={`font-mono font-semibold ${passes ? 'text-green' : 'text-orange'}`}>
        {value.toFixed(2)}
        {passes ? ' ✓' : ' ✗'}
      </span>
    </div>
  )
}

function MergeExample({ candidate, delay }: { candidate: MergeCandidate; delay: number }) {
  return (
    <motion.div
      className="rounded-xl bg-surface-2 border border-border p-5 space-y-4"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.5, delay }}
    >
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex gap-2 flex-wrap">
          {candidate.variants.map(v => (
            <motion.span
              key={v}
              className="px-2 py-1 rounded-md bg-surface-3 border border-border text-xs font-mono text-gray-400"
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: delay + 0.2 }}
            >
              {v}
            </motion.span>
          ))}
        </div>
        <span className="text-gray-600 text-sm">→</span>
        <motion.span
          className="px-3 py-1 rounded-lg bg-accent/15 border border-accent/40 text-accent text-sm font-semibold"
          initial={{ opacity: 0, scale: 0.85 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: delay + 0.5 }}
        >
          {candidate.canonical}
        </motion.span>
      </div>

      <motion.div
        className="space-y-2 pt-2 border-t border-border"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: delay + 0.6 }}
      >
        <ScoreBadge label="Fuzzy match" value={candidate.fuzzyScore} threshold={FUZZY_THRESHOLD} />
        <ScoreBadge label="Embedding similarity" value={candidate.embeddingScore} threshold={EMBEDDING_THRESHOLD} />
        <div className="flex items-center justify-between text-xs pt-1">
          <span className="text-gray-600">Thresholds: fuzzy ≥ {FUZZY_THRESHOLD}, embedding ≥ {EMBEDDING_THRESHOLD}</span>
        </div>
      </motion.div>
    </motion.div>
  )
}

export const ResolutionPanel = memo(function ResolutionPanel() {
  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-2 gap-4">
        {MERGE_CANDIDATES.map((c, i) => (
          <MergeExample key={c.canonical} candidate={c} delay={i * 0.25} />
        ))}
      </div>
      <motion.div
        className="rounded-lg bg-surface-2 border border-border px-4 py-3 text-sm text-gray-400 text-center"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.8 }}
      >
        Resolved <strong className="text-white">8 raw mentions</strong> → <strong className="text-white">6 canonical entities</strong>
      </motion.div>
    </div>
  )
})
