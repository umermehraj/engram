import { memo } from 'react'
import { motion } from 'framer-motion'
import { TEMPORAL_FACTS } from '../../data/pipelineData'

interface TimelineEvent {
  date: string
  label: string
  subject: string
  predicate: string
  object: string
  type: 'active' | 'invalidated' | 'conflict'
  note?: string
}

const EVENTS: TimelineEvent[] = [
  {
    date: 'Mar 1, 2025',
    label: 'Decision recorded',
    ...TEMPORAL_FACTS[0],
    type: 'active',
  },
  {
    date: 'Mar 15, 2025',
    label: 'Conflict detected',
    subject: '',
    predicate: '',
    object: '',
    type: 'conflict',
    note: 'New fact contradicts existing belief — initiating temporal supersession',
  },
  {
    date: 'Mar 15, 2025',
    label: 'Fact invalidated',
    ...TEMPORAL_FACTS[0],
    type: 'invalidated',
    note: 'invalid_from = Mar 15, 2025',
  },
  {
    date: 'Mar 15, 2025',
    label: 'New fact stored',
    ...TEMPORAL_FACTS[1],
    type: 'active',
  },
]

function TimelineDot({ type }: { type: TimelineEvent['type'] }) {
  const color =
    type === 'active' ? 'bg-green border-green/50' :
    type === 'conflict' ? 'bg-orange border-orange/50' :
    'bg-gray-600 border-gray-500'
  return (
    <div className={`w-3 h-3 rounded-full border-2 shrink-0 mt-1.5 ${color}`} />
  )
}

function FactDisplay({ subject, predicate, object, strikethrough }: {
  subject: string; predicate: string; object: string; strikethrough: boolean
}) {
  if (!subject) return null
  return (
    <span className={`font-mono text-xs ${strikethrough ? 'line-through opacity-40' : 'text-gray-300'}`}>
      {subject} —[{predicate}]→ {object}
    </span>
  )
}

export const TemporalPanel = memo(function TemporalPanel() {
  return (
    <div className="space-y-6">
      <div className="relative">
        {/* vertical line */}
        <div className="absolute left-5 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-0">
          {EVENTS.map((event, i) => (
            <motion.div
              key={i}
              className="relative flex gap-4 pb-6 last:pb-0"
              initial={{ opacity: 0, x: -12 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.4, delay: i * 0.3 }}
            >
              <div className="z-10">
                <TimelineDot type={event.type} />
              </div>
              <div className="flex-1 rounded-xl bg-surface-2 border border-border p-4 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <p className={`text-sm font-semibold ${
                      event.type === 'active' ? 'text-white' :
                      event.type === 'conflict' ? 'text-orange' :
                      'text-gray-500'
                    }`}>
                      {event.label}
                    </p>
                    <FactDisplay
                      subject={event.subject}
                      predicate={event.predicate}
                      object={event.object}
                      strikethrough={event.type === 'invalidated'}
                    />
                  </div>
                  <span className="text-xs text-gray-600 shrink-0 font-mono">{event.date}</span>
                </div>
                {event.note && (
                  <p className={`text-xs ${
                    event.type === 'conflict' ? 'text-orange/80' :
                    event.type === 'invalidated' ? 'text-gray-600 font-mono' :
                    'text-gray-500'
                  }`}>
                    {event.note}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.div
        className="rounded-xl bg-accent/5 border border-accent/20 p-4 text-sm text-gray-400"
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 1.3, duration: 0.4 }}
      >
        <span className="text-accent font-semibold">Old facts are never deleted</span> — just versioned.{' '}
        <code className="text-xs bg-surface-3 px-1.5 py-0.5 rounded text-gray-300">invalid_from</code> marks
        when a belief changed, preserving the full history for temporal queries.
      </motion.div>
    </div>
  )
})
