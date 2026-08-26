import { memo, useState } from 'react'
import { motion } from 'framer-motion'
import { PipelinePanel } from './PipelinePanel'
import { InputPanel } from './InputPanel'
import { ExtractionPanel } from './ExtractionPanel'
import { ResolutionPanel } from './ResolutionPanel'
import { TemporalPanel } from './TemporalPanel'
import { GraphPanel } from './GraphPanel'
import { ClassificationPanel } from './ClassificationPanel'
import { RetrievalPanel } from './RetrievalPanel'
import { ResultPanel } from './ResultPanel'

const PANELS = [
  {
    number: 1,
    title: 'Raw Input',
    subtitle: 'A conversation about switching backend frameworks. Engram ingests it, extracts structured facts, and builds a knowledge graph.',
  },
  {
    number: 2,
    title: 'Fact Extraction + Gleaning',
    subtitle: 'An LLM extracts subject–predicate–object triples. A second pass (gleaning) catches facts missed on the first read.',
  },
  {
    number: 3,
    title: 'Entity Resolution',
    subtitle: 'Raw mentions are deduplicated into canonical entities using fuzzy matching and embedding similarity.',
  },
  {
    number: 4,
    title: 'Temporal Linking',
    subtitle: 'Contradicting facts are versioned rather than overwritten. Every belief has a valid_from timestamp.',
  },
  {
    number: 5,
    title: 'Knowledge Graph',
    subtitle: 'Entities become nodes, facts become typed edges. Edge weight reflects relationship signal strength.',
  },
  {
    number: 6,
    title: 'Query Classification',
    subtitle: 'Before searching, Engram classifies the query type to adjust retrieval weights across the three search paths.',
  },
  {
    number: 7,
    title: 'Parallel Retrieval + RRF Fusion',
    subtitle: 'Vector, graph, and temporal search run in parallel. Results are merged via Reciprocal Rank Fusion with multi-source bonuses.',
  },
  {
    number: 8,
    title: 'Context Assembly',
    subtitle: 'Top-ranked entities are packed into a token-budgeted context block, annotated by source, and handed to the LLM.',
  },
]

const PANEL_CHILDREN = [
  <InputPanel />,
  <ExtractionPanel />,
  <ResolutionPanel />,
  <TemporalPanel />,
  <GraphPanel />,
  <ClassificationPanel />,
  <RetrievalPanel />,
  <ResultPanel />,
]

export const PipelineVisualizer = memo(function PipelineVisualizer() {
  const [activePanel, setActivePanel] = useState(1)

  return (
    <div className="relative">
      {/* Progress indicator */}
      <div className="fixed right-4 top-1/2 -translate-y-1/2 z-40 hidden lg:flex flex-col gap-2">
        {PANELS.map(p => (
          <motion.button
            key={p.number}
            onClick={() => {
              document.getElementById(`pipeline-panel-${p.number}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }}
            title={p.title}
            className={`w-2 h-2 rounded-full transition-all duration-200 ${
              activePanel === p.number
                ? 'bg-accent w-2.5 h-2.5'
                : 'bg-border hover:bg-gray-500'
            }`}
          />
        ))}
      </div>

      {PANELS.map((panel, i) => (
        <div key={panel.number} id={`pipeline-panel-${panel.number}`}>
          <PipelinePanel
            number={panel.number}
            title={panel.title}
            subtitle={panel.subtitle}
            onVisible={setActivePanel}
          >
            {PANEL_CHILDREN[i]}
          </PipelinePanel>
          {i < PANELS.length - 1 && (
            <div className="flex justify-center py-2">
              <motion.div
                className="flex flex-col items-center gap-1 text-gray-700"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
              >
                <div className="w-px h-6 bg-border" />
                <svg width="10" height="6" viewBox="0 0 10 6" fill="currentColor">
                  <path d="M5 6L0 0h10z" />
                </svg>
              </motion.div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
})
