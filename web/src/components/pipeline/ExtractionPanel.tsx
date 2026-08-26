import { memo } from 'react'
import { motion } from 'framer-motion'
import { EXTRACTED_FACTS, type ExtractedFact } from '../../data/pipelineData'

const TYPE_COLOR: Record<string, string> = {
  person: 'text-orange border-orange/30 bg-orange/10',
  tool: 'text-accent border-accent/30 bg-accent/10',
  concept: 'text-green border-green/30 bg-green/10',
}

function FactCard({ fact, isGleaned }: { fact: ExtractedFact; isGleaned: boolean }) {
  return (
    <div
      className={`rounded-lg border p-3 space-y-2 ${
        isGleaned ? 'border-green/40 border-dashed bg-green/5' : 'border-border bg-surface-3'
      }`}
    >
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${TYPE_COLOR[fact.subjectType] ?? 'text-gray-400'}`}>
          {fact.subject}
        </span>
        <span className="text-xs text-gray-500 font-mono">—[{fact.predicate}]→</span>
        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${TYPE_COLOR[fact.objectType] ?? 'text-gray-400'}`}>
          {fact.object}
        </span>
        {isGleaned && (
          <span className="text-xs text-green font-semibold ml-auto">gleaned</span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1 rounded-full bg-surface-2">
          <div
            className="h-full rounded-full bg-accent/60"
            style={{ width: `${fact.confidence * 100}%` }}
          />
        </div>
        <span className="text-xs text-gray-500 font-mono">{fact.confidence.toFixed(2)}</span>
      </div>
    </div>
  )
}

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
}

const item = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35 } },
}

export const ExtractionPanel = memo(function ExtractionPanel() {
  const round1 = EXTRACTED_FACTS.filter(f => f.gleanRound === 0)
  const round2 = EXTRACTED_FACTS.filter(f => f.gleanRound === 1)

  return (
    <div className="space-y-6">
      <motion.div
        className="space-y-3"
        variants={container}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.1 }}
      >
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Round 1 — Initial Extraction ({round1.length} facts)
        </p>
        <div className="grid sm:grid-cols-2 gap-2">
          {round1.map((fact, i) => (
            <motion.div key={i} variants={item}>
              <FactCard fact={fact} isGleaned={false} />
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div
        className="space-y-3"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.7, duration: 0.4 }}
      >
        <div className="flex items-center gap-2">
          <div className="h-px flex-1 bg-border" />
          <p className="text-xs font-semibold text-green uppercase tracking-wider px-2">
            Gleaning Round 2 — Re-extraction pass
          </p>
          <div className="h-px flex-1 bg-border" />
        </div>
        <motion.div
          className="grid sm:grid-cols-2 gap-2"
          variants={container}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {round2.map((fact, i) => (
            <motion.div key={i} variants={item}>
              <FactCard fact={fact} isGleaned />
            </motion.div>
          ))}
        </motion.div>
        <motion.div
          className="rounded-lg bg-green/5 border border-green/20 px-4 py-3 text-sm text-green"
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 1.0, duration: 0.4 }}
        >
          Gleaning found <strong>{round2.length} additional facts</strong> the LLM missed on first pass.
        </motion.div>
      </motion.div>
    </div>
  )
})
