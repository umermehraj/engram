import { memo } from 'react'
import { motion } from 'framer-motion'
import { CONVERSATION_LINES, ENTITY_COLOR_MAP } from '../../data/pipelineData'

const ENTITIES = Object.keys(ENTITY_COLOR_MAP)
const ENTITY_REGEX = new RegExp(`(${ENTITIES.join('|')})`, 'g')

function highlightText(text: string) {
  const parts = text.split(ENTITY_REGEX)
  return parts.map((part, i) => {
    const color = ENTITY_COLOR_MAP[part]
    if (color) {
      return (
        <span key={i} className={`${color} font-semibold underline decoration-dotted underline-offset-2`}>
          {part}
        </span>
      )
    }
    return <span key={i}>{part}</span>
  })
}

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.2 } },
}

const line = {
  hidden: { opacity: 0, x: -16 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.4 } },
}

export const InputPanel = memo(function InputPanel() {
  return (
    <div className="relative rounded-xl bg-surface-2 border border-border p-6">
      <span className="absolute top-4 right-4 text-xs font-semibold text-gray-500 bg-surface-3 border border-border px-2 py-1 rounded-full">
        Raw Conversation
      </span>
      <motion.div
        className="space-y-3 font-mono text-sm"
        variants={container}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
      >
        {CONVERSATION_LINES.map((l, i) => (
          <motion.div key={i} variants={line} className="flex gap-3">
            <span
              className={`font-semibold shrink-0 ${ENTITY_COLOR_MAP[l.speaker] ?? 'text-gray-400'}`}
            >
              {l.speaker}:
            </span>
            <span className="text-gray-300 leading-relaxed">{highlightText(l.text)}</span>
          </motion.div>
        ))}
      </motion.div>

      <motion.div
        className="mt-6 flex flex-wrap gap-3 text-xs"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1.2, duration: 0.4 }}
      >
        {(['person', 'tool', 'concept'] as const).map(type => (
          <span key={type} className="flex items-center gap-1.5 text-gray-500">
            <span
              className={`w-2 h-2 rounded-full ${
                type === 'person' ? 'bg-orange' : type === 'tool' ? 'bg-accent' : 'bg-green'
              }`}
            />
            {type}
          </span>
        ))}
      </motion.div>
    </div>
  )
})
