import { memo } from 'react'
import { motion } from 'framer-motion'
import { ASSEMBLED_CONTEXT, RETRIEVAL_METADATA, type SourceBlock } from '../../data/pipelineData'

const SOURCE_STYLES: Record<string, { label: string; color: string; bg: string }> = {
  vector: { label: 'vector', color: 'text-accent', bg: 'bg-accent/15 border-accent/30' },
  graph: { label: 'graph', color: 'text-green', bg: 'bg-green/15 border-green/30' },
  temporal: { label: 'temporal', color: 'text-orange', bg: 'bg-orange/15 border-orange/30' },
  'graph+temporal': { label: 'graph+temporal', color: 'text-purple', bg: 'bg-purple/15 border-purple/30' },
}

function ContextBlock({ block, index }: { block: SourceBlock; index: number }) {
  const style = SOURCE_STYLES[block.source]
  return (
    <motion.div
      className="flex items-start gap-3"
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35, delay: 0.2 + index * 0.12 }}
    >
      <div className="flex-1 text-sm text-gray-300 leading-relaxed pt-0.5">{block.text}</div>
      <span className={`shrink-0 text-xs font-mono px-2 py-0.5 rounded-full border ${style.bg} ${style.color}`}>
        {style.label}
      </span>
    </motion.div>
  )
}

export const ResultPanel = memo(function ResultPanel() {
  return (
    <div className="space-y-6">
      <motion.div
        className="rounded-xl bg-surface-2 border border-border p-6 space-y-4"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
      >
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Assembled Context</p>
        <div className="space-y-3 divide-y divide-border/40">
          {ASSEMBLED_CONTEXT.map((block, i) => (
            <div key={i} className={i > 0 ? 'pt-3' : ''}>
              <ContextBlock block={block} index={i} />
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        className="grid grid-cols-2 sm:grid-cols-4 gap-3"
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.9, duration: 0.4 }}
      >
        {[
          { label: 'Tokens', value: RETRIEVAL_METADATA.tokens.toString() },
          { label: 'Retrieval', value: `${RETRIEVAL_METADATA.retrieval}ms` },
          { label: 'Blocks', value: RETRIEVAL_METADATA.blocks.toString() },
          { label: 'Multi-source', value: RETRIEVAL_METADATA.multiSource.toString() },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-xl bg-surface-2 border border-border p-3 text-center">
            <p className="text-xl font-bold text-white">{value}</p>
            <p className="text-xs text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </motion.div>

      <motion.div
        className="rounded-xl bg-green/5 border border-green/20 p-4 text-sm"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 1.1, duration: 0.4 }}
      >
        <span className="text-green font-semibold">No hallucination about Django being current</span>
        <span className="text-gray-400"> — temporal versioning caught the update and applied recency decay to the invalidated fact.</span>
      </motion.div>
    </div>
  )
})
