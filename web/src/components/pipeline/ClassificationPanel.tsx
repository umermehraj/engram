import { memo, useState } from 'react'
import { motion } from 'framer-motion'
import { CLASSIFICATION_EXAMPLES } from '../../data/pipelineData'

const TYPE_COLOR: Record<string, string> = {
  FACTUAL: 'text-accent border-accent/40 bg-accent/10',
  TEMPORAL: 'text-orange border-orange/40 bg-orange/10',
  PREFERENCE: 'text-purple border-purple/40 bg-purple/10',
}

const BAR_COLOR: Record<string, string> = {
  vector: 'bg-accent',
  graph: 'bg-green',
  temporal: 'bg-orange',
}

interface WeightBarProps {
  label: string
  value: number
  delay: number
}

function WeightBar({ label, value, delay }: WeightBarProps) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className={`font-medium ${label === 'vector' ? 'text-accent' : label === 'graph' ? 'text-green' : 'text-orange'}`}>
          {label}
        </span>
        <span className="text-gray-500 font-mono">{value.toFixed(2)}</span>
      </div>
      <div className="h-2 rounded-full bg-surface-3 overflow-hidden">
        <motion.div
          className={`h-full rounded-full origin-left ${BAR_COLOR[label]}`}
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: value }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: 'easeOut', delay }}
        />
      </div>
    </div>
  )
}

export const ClassificationPanel = memo(function ClassificationPanel() {
  const [activeExample, setActiveExample] = useState(0)
  const example = CLASSIFICATION_EXAMPLES[activeExample]

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        {CLASSIFICATION_EXAMPLES.map((_ex, i) => (
          <button
            key={i}
            onClick={() => setActiveExample(i)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              activeExample === i
                ? 'bg-surface-3 border-border text-white'
                : 'bg-transparent border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            Example {i + 1}
          </button>
        ))}
      </div>

      <motion.div
        key={activeExample}
        className="space-y-5"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="rounded-xl bg-surface-2 border border-border p-5 space-y-4">
          <div className="space-y-2">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Query</p>
            <p className="text-white font-mono text-sm">"{example.query}"</p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">Classified as</span>
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${TYPE_COLOR[example.type] ?? 'text-gray-400'}`}>
              {example.type}
            </span>
          </div>
        </div>

        <div className="rounded-xl bg-surface-2 border border-border p-5 space-y-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Retrieval Weights</p>
          <div className="space-y-3">
            {(['vector', 'graph', 'temporal'] as const).map((key, i) => (
              <WeightBar
                key={key}
                label={key}
                value={example.weights[key]}
                delay={0.1 + i * 0.15}
              />
            ))}
          </div>
        </div>

        <motion.p
          className="text-sm text-gray-400 px-1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          {example.explanation}
        </motion.p>
      </motion.div>
    </div>
  )
})
