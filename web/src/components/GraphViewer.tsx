import { useEffect, useRef } from 'react'
import { Network, type Options } from 'vis-network'
import { DataSet } from 'vis-data'
import type { GraphData } from '../types'

const ENTITY_COLORS: Record<string, string> = {
  person: '#4CAF50',
  project: '#2196F3',
  tool: '#FF9800',
  concept: '#9C27B0',
  preference: '#E91E63',
  organization: '#00BCD4',
  document: '#FFD54F',
  conversation: '#81C784',
  image: '#CE93D8',
  video: '#EF5350',
  audio: '#42A5F5',
  file: '#A1887F',
  webpage: '#26C6DA',
  code: '#66BB6A',
}

const ENTITY_SHAPES: Record<string, string> = {
  person: 'dot', project: 'dot', tool: 'dot',
  concept: 'diamond', preference: 'star', organization: 'dot',
  document: 'square', conversation: 'triangle',
  image: 'square', video: 'triangleDown',
  audio: 'diamond', file: 'square',
  webpage: 'triangle', code: 'square',
}

const EDGE_COLORS: Record<string, string> = {
  decided: '#F44336', prefers: '#E91E63', believes: '#9C27B0',
  works_on: '#2196F3', replaced: '#FF5722',
  mentioned: '#555', asked_about: '#555',
  related_to: '#90CAF9', depends_on: '#FFB74D', part_of: '#81C784',
  contradicts: '#F44336', supersedes: '#FF9800', derived_from: '#78909C',
}

const META_EDGES = new Set(['contradicts', 'supersedes', 'derived_from'])

interface GraphViewerProps {
  data: GraphData
  height?: string
  onNodeClick?: (nodeId: string) => void
}

export function GraphViewer({ data, height = '500px', onNodeClick }: GraphViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const networkRef = useRef<Network | null>(null)

  useEffect(() => {
    if (!containerRef.current || data.nodes.length === 0) return

    const nodes = new DataSet(
      data.nodes.map((n) => {
        const isSource = ['document', 'conversation', 'image', 'video', 'audio', 'file', 'webpage', 'code'].includes(n.entity_type)
        return {
          id: n.id,
          label: n.name,
          color: {
            background: ENTITY_COLORS[n.entity_type] ?? '#757575',
            border: ENTITY_COLORS[n.entity_type] ?? '#757575',
            highlight: { background: '#fff', border: ENTITY_COLORS[n.entity_type] ?? '#757575' },
          },
          shape: ENTITY_SHAPES[n.entity_type] ?? 'dot',
          size: isSource ? 28 : 14 + n.confidence * 18,
          title: `<b>${n.name}</b><br/>Type: ${n.entity_type}<br/>Confidence: ${n.confidence.toFixed(2)}<br/>${n.summary}`,
          font: { color: '#e0e0e0', size: 13 },
          borderWidth: 2,
          borderWidthSelected: 4,
        }
      })
    )

    const nodeIds = new Set(data.nodes.map((n) => n.id))
    const edges = new DataSet(
      data.edges
        .filter((e) => nodeIds.has(e.from_id) && nodeIds.has(e.to_id))
        .map((e, i) => ({
          id: `edge-${i}`,
          from: e.from_id,
          to: e.to_id,
          label: e.rel_type,
          color: { color: EDGE_COLORS[e.rel_type] ?? '#757575', opacity: 0.8 },
          width: ['decided', 'prefers', 'replaced', 'works_on'].includes(e.rel_type) ? 2.5 : 1.5,
          dashes: META_EDGES.has(e.rel_type),
          arrows: 'to',
          font: { color: '#666', size: 10, align: 'middle' },
          title: `<b>${e.rel_type}</b><br/>${e.summary}<br/>Confidence: ${e.confidence.toFixed(2)}`,
        }))
    )

    const options: Options = {
      physics: {
        barnesHut: {
          gravitationalConstant: -6000,
          centralGravity: 0.3,
          springLength: 180,
          springConstant: 0.04,
          damping: 0.09,
        },
        maxVelocity: 50,
        minVelocity: 0.1,
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        navigationButtons: false,
        keyboard: true,
        zoomView: true,
        dragView: true,
      },
      edges: {
        smooth: { enabled: true, type: 'continuous', roundness: 0.5 },
      },
    }

    const network = new Network(containerRef.current, { nodes, edges }, options)
    networkRef.current = network

    if (onNodeClick) {
      network.on('click', (params) => {
        if (params.nodes.length > 0) {
          onNodeClick(params.nodes[0] as string)
        }
      })
    }

    return () => {
      network.destroy()
      networkRef.current = null
    }
  }, [data, onNodeClick])

  return (
    <div className="relative">
      <div
        ref={containerRef}
        style={{ height }}
        className="w-full rounded-xl border border-border bg-surface-2"
      />
      <Legend />
    </div>
  )
}

function Legend() {
  const entityTypes = [
    { type: 'person', label: 'Person' },
    { type: 'project', label: 'Project' },
    { type: 'tool', label: 'Tool' },
    { type: 'concept', label: 'Concept' },
  ]
  const sourceTypes = [
    { type: 'document', label: 'Document' },
    { type: 'conversation', label: 'Conversation' },
    { type: 'image', label: 'Image' },
    { type: 'code', label: 'Code' },
    { type: 'audio', label: 'Audio' },
    { type: 'webpage', label: 'Webpage' },
  ]

  return (
    <div className="absolute top-3 right-3 rounded-lg border border-border bg-surface-2/90 backdrop-blur-sm p-3 text-xs space-y-2 pointer-events-none">
      <div className="font-semibold text-gray-300">Entities</div>
      {entityTypes.map(({ type, label }) => (
        <div key={type} className="flex items-center gap-1.5">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ background: ENTITY_COLORS[type] }}
          />
          <span className="text-gray-400">{label}</span>
        </div>
      ))}
      <div className="font-semibold text-gray-300 pt-1">Sources</div>
      {sourceTypes.map(({ type, label }) => (
        <div key={type} className="flex items-center gap-1.5">
          <span
            className="inline-block w-2.5 h-2.5 rounded-sm"
            style={{ background: ENTITY_COLORS[type] }}
          />
          <span className="text-gray-400">{label}</span>
        </div>
      ))}
    </div>
  )
}
