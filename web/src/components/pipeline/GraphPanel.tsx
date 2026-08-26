import { memo, useState } from 'react'
import { motion } from 'framer-motion'
import { GRAPH_NODES, GRAPH_EDGES } from '../../data/pipelineData'

const NODE_COLOR: Record<string, string> = {
  person: '#fb923c',
  tool: '#6366f1',
  concept: '#4ade80',
  project: '#a78bfa',
}

const NODE_BG: Record<string, string> = {
  person: 'rgba(251,146,60,0.15)',
  tool: 'rgba(99,102,241,0.15)',
  concept: 'rgba(74,222,128,0.15)',
  project: 'rgba(167,139,250,0.15)',
}

function edgeColor(weight: number, active: boolean): string {
  if (!active) return '#374151'
  if (weight >= 0.9) return '#ef4444'
  if (weight >= 0.7) return '#6366f1'
  if (weight >= 0.4) return '#6b7280'
  return '#4b5563'
}

function edgeWidth(weight: number): number {
  if (weight >= 0.9) return 2.5
  if (weight >= 0.7) return 1.8
  return 1
}

function getNode(id: string) {
  return GRAPH_NODES.find(n => n.id === id)!
}

function midpoint(x1: number, y1: number, x2: number, y2: number) {
  return { mx: (x1 + x2) / 2, my: (y1 + y2) / 2 }
}

export const GraphPanel = memo(function GraphPanel() {
  const [hovered, setHovered] = useState<string | null>(null)

  return (
    <div className="rounded-xl bg-surface-2 border border-border overflow-hidden">
      <svg
        viewBox="0 0 700 450"
        className="w-full"
        style={{ maxHeight: '480px' }}
        aria-label="Engram knowledge graph"
      >
        <defs>
          <marker id="arrow-active" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#6366f1" />
          </marker>
          <marker id="arrow-strong" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#ef4444" />
          </marker>
          <marker id="arrow-weak" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#6b7280" />
          </marker>
          <marker id="arrow-inactive" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#374151" />
          </marker>
        </defs>

        {/* Edges */}
        {GRAPH_EDGES.map((edge, i) => {
          const from = getNode(edge.from)
          const to = getNode(edge.to)
          if (!from || !to) return null
          const { mx, my } = midpoint(from.x, from.y, to.x, to.y)
          const color = edgeColor(edge.weight, edge.active)
          const width = edgeWidth(edge.weight)
          const markerId = !edge.active ? 'arrow-inactive' : edge.weight >= 0.9 ? 'arrow-strong' : edge.weight >= 0.7 ? 'arrow-active' : 'arrow-weak'

          return (
            <motion.g key={i}>
              <motion.path
                d={`M ${from.x} ${from.y} L ${to.x} ${to.y}`}
                fill="none"
                stroke={color}
                strokeWidth={width}
                strokeDasharray={!edge.active ? '6,4' : edge.weight <= 0.35 ? '3,3' : undefined}
                opacity={!edge.active ? 0.25 : 1}
                markerEnd={`url(#${markerId})`}
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.4 + i * 0.06 }}
              />
              <motion.text
                x={mx}
                y={my - 5}
                textAnchor="middle"
                fontSize="9"
                fill={edge.active ? '#9ca3af' : '#4b5563'}
                opacity={!edge.active ? 0.5 : 1}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: !edge.active ? 0.5 : 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.9 + i * 0.05 }}
              >
                {edge.label}
              </motion.text>
            </motion.g>
          )
        })}

        {/* Nodes */}
        {GRAPH_NODES.map((node, i) => {
          const color = NODE_COLOR[node.type]
          const bg = NODE_BG[node.type]
          const isHovered = hovered === node.id
          return (
            <motion.g
              key={node.id}
              style={{ cursor: 'pointer' }}
              initial={{ opacity: 0, scale: 0 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.1 }}
              onHoverStart={() => setHovered(node.id)}
              onHoverEnd={() => setHovered(null)}
            >
              <circle
                cx={node.x}
                cy={node.y}
                r={node.size + (isHovered ? 3 : 0)}
                fill={bg}
                stroke={color}
                strokeWidth={isHovered ? 2.5 : 1.5}
                style={{ transition: 'r 0.15s, stroke-width 0.15s' }}
              />
              <text
                x={node.x}
                y={node.y + node.size + 12}
                textAnchor="middle"
                fontSize="10"
                fill={color}
                fontWeight="500"
              >
                {node.label}
              </text>
            </motion.g>
          )
        })}
      </svg>

      {/* Legend */}
      <div className="border-t border-border px-4 py-3 flex flex-wrap gap-4 text-xs text-gray-500">
        {(['person', 'tool', 'concept'] as const).map(type => (
          <span key={type} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: NODE_COLOR[type] }} />
            {type}
          </span>
        ))}
        <span className="flex items-center gap-1.5 ml-auto">
          <span className="inline-block w-5 h-0.5 bg-red-500" />
          high signal
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-5 h-px bg-gray-600 border-dashed border-t border-gray-600" style={{ borderStyle: 'dashed' }} />
          invalidated
        </span>
      </div>
    </div>
  )
})
