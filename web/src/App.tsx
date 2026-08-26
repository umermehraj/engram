import { lazy, Suspense, useState } from 'react'
import { GraphViewer } from './components/GraphViewer'
import { SearchPanel } from './components/SearchPanel'
import { ComparisonTable } from './components/ComparisonTable'
import { Architecture } from './components/Architecture'
import { Section } from './components/Section'
import { HERO_GRAPHS } from './data/heroGraphData'

const PipelineVisualizer = lazy(() =>
  import('./components/pipeline/PipelineVisualizer').then(m => ({ default: m.PipelineVisualizer }))
)

const TECH_STACK = [
  { name: 'Python', color: '#3776AB' },
  { name: 'Kuzu', color: '#FF9800' },
  { name: 'LanceDB', color: '#4CAF50' },
  { name: 'FastAPI', color: '#009688' },
  { name: 'sentence-transformers', color: '#E91E63' },
  { name: 'React', color: '#61DAFB' },
  { name: 'D3 / vis.js', color: '#F4A460' },
]

function App() {
  const [heroTab, setHeroTab] = useState(0)

  return (
    <div className="min-h-screen bg-[#0a0a1a]">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-[#0a0a1a]/80 backdrop-blur-md border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <span className="text-lg font-bold text-white tracking-tight">Engram</span>
          <div className="hidden md:flex gap-6 text-sm text-gray-400">
            <a href="#pipeline" className="hover:text-white transition-colors">Pipeline</a>
            <a href="#graph" className="hover:text-white transition-colors">Graph</a>
            <a href="#search" className="hover:text-white transition-colors">Search</a>
            <a href="#compare" className="hover:text-white transition-colors">Compare</a>
            <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
            <a
              href="https://github.com/Kaboom2025/engram"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className="pt-28 pb-8 px-6 text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/30 text-accent text-sm">
            Hybrid Memory for AI Agents
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white leading-tight tracking-tight">
            Knowledge Graph +{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-purple">
              Vector Search
            </span>{' '}
            + Temporal Awareness
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            When you ask <em className="text-gray-300">"what backend framework are we using?"</em>,
            naive RAG returns documents that mention frameworks. Engram knows that
            Django was <strong className="text-orange">replaced</strong> by FastAPI last week &mdash;
            a temporal, graph-structured fact that vector similarity alone misses.
          </p>
        </div>
      </header>

      {/* Hero Graph */}
      <div id="graph" className="px-6 md:px-12 pb-8">
        <div className="max-w-5xl mx-auto space-y-3">
          <div className="flex items-center gap-1">
            {HERO_GRAPHS.map((g, i) => (
              <button
                key={g.id}
                onClick={() => setHeroTab(i)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
                  heroTab === i
                    ? 'bg-surface-2 border-border text-white'
                    : 'bg-transparent border-transparent text-gray-500 hover:text-gray-300'
                }`}
              >
                {g.label}
              </button>
            ))}
            <span className="ml-2 text-xs text-gray-600">{HERO_GRAPHS[heroTab].description}</span>
          </div>
          <GraphViewer data={HERO_GRAPHS[heroTab].data} height="500px" />
        </div>
      </div>

      {/* Pipeline Visualizer */}
      <section id="pipeline" className="py-16 px-6 md:px-12 border-t border-border">
        <div className="max-w-4xl mx-auto mb-8">
          <h2 className="text-3xl font-bold text-white">How Engram Processes Data</h2>
          <p className="mt-2 text-gray-400">
            An interactive walkthrough of the full ingestion and retrieval pipeline — from raw text to grounded LLM context.
          </p>
        </div>
        <Suspense
          fallback={
            <div className="h-64 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
            </div>
          }
        >
          <PipelineVisualizer />
        </Suspense>
      </section>

      {/* The Problem */}
      <Section id="problem" title="The Problem">
        <div className="rounded-xl bg-surface-2 border border-border p-6 space-y-4">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Naive RAG</h3>
              <div className="font-mono text-sm text-gray-500 space-y-1">
                <p>1. Embed query</p>
                <p>2. Find similar chunks by cosine distance</p>
                <p>3. Return top-k chunks</p>
              </div>
              <p className="text-sm text-gray-500">
                Returns documents that mention Django <em>and</em> FastAPI.
                No way to know which is current.
              </p>
            </div>
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-accent uppercase tracking-wider">Engram Hybrid</h3>
              <div className="font-mono text-sm text-gray-300 space-y-1">
                <p>1. <span className="text-accent">Vector search</span> &rarr; FastAPI, Django, Flask</p>
                <p>2. <span className="text-green">Graph traversal</span> &rarr; Saalik --[decided]--&gt; FastAPI</p>
                <p>3. <span className="text-orange">Temporal layer</span> &rarr; Django was invalidated last week</p>
                <p>4. <span className="text-purple">RRF fusion</span> &rarr; FastAPI scores 3x higher</p>
              </div>
              <p className="text-sm text-gray-400">
                Grounded context, not just similar chunks.
              </p>
            </div>
          </div>
        </div>
      </Section>

      {/* Search */}
      <Section
        id="search"
        title="Try a Query"
        subtitle="Type a question or click a suggestion. See how vector, graph, and temporal signals fuse."
      >
        <SearchPanel />
      </Section>

      {/* Compare */}
      <Section
        id="compare"
        title="Feature Comparison"
        subtitle="How Engram stacks up against other memory systems."
      >
        <div className="rounded-xl bg-surface-2 border border-border overflow-hidden">
          <ComparisonTable />
        </div>
      </Section>

      {/* Architecture */}
      <Section
        id="architecture"
        title="How It Works"
        subtitle="Three-layer retrieval with weighted Reciprocal Rank Fusion."
      >
        <Architecture />
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div className="rounded-xl bg-surface-2 border border-border p-4 space-y-2">
            <div className="text-accent font-semibold">Kuzu Graph DB</div>
            <p className="text-gray-400">
              Embedded graph with append-only edges. <code className="text-xs bg-surface-3 px-1 rounded">valid_from</code> / <code className="text-xs bg-surface-3 px-1 rounded">invalid_from</code> for temporal versioning.
            </p>
          </div>
          <div className="rounded-xl bg-surface-2 border border-border p-4 space-y-2">
            <div className="text-green font-semibold">LanceDB Vectors</div>
            <p className="text-gray-400">
              Embedded vector store. ANN search over entity summaries. 384 / 1536 / 3072-dim.
            </p>
          </div>
          <div className="rounded-xl bg-surface-2 border border-border p-4 space-y-2">
            <div className="text-orange font-semibold">Temporal Layer</div>
            <p className="text-gray-400">
              Exponential recency decay (half-life ~35h). Session facts scored highest. Recently-referenced entities boosted.
            </p>
          </div>
        </div>

        <div className="rounded-xl bg-surface-2 border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-gray-400 font-medium">Query Type</th>
                <th className="py-3 px-4 text-accent font-medium">Vector</th>
                <th className="py-3 px-4 text-green font-medium">Graph</th>
                <th className="py-3 px-4 text-orange font-medium">Temporal</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              <tr className="border-b border-border/50">
                <td className="py-2 px-4">Temporal ("when did we...")</td>
                <td className="py-2 px-4 text-center">0.20</td>
                <td className="py-2 px-4 text-center">0.30</td>
                <td className="py-2 px-4 text-center font-bold text-orange">0.50</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 px-4">Factual ("what is...")</td>
                <td className="py-2 px-4 text-center">0.20</td>
                <td className="py-2 px-4 text-center font-bold text-green">0.60</td>
                <td className="py-2 px-4 text-center">0.20</td>
              </tr>
              <tr className="border-b border-border/50">
                <td className="py-2 px-4">Preference ("does Alice like...")</td>
                <td className="py-2 px-4 text-center font-bold text-accent">0.50</td>
                <td className="py-2 px-4 text-center">0.30</td>
                <td className="py-2 px-4 text-center">0.20</td>
              </tr>
              <tr>
                <td className="py-2 px-4">Default</td>
                <td className="py-2 px-4 text-center">0.35</td>
                <td className="py-2 px-4 text-center">0.40</td>
                <td className="py-2 px-4 text-center">0.25</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      {/* Tech Stack */}
      <Section id="stack" title="Tech Stack">
        <div className="flex flex-wrap gap-3">
          {TECH_STACK.map(({ name, color }) => (
            <span
              key={name}
              className="px-4 py-2 rounded-xl text-sm font-medium border"
              style={{
                borderColor: `${color}40`,
                color,
                background: `${color}10`,
              }}
            >
              {name}
            </span>
          ))}
        </div>
      </Section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-border text-center text-sm text-gray-600">
        <p>Built by Saalik &middot; MIT License &middot; 2025</p>
      </footer>
    </div>
  )
}

export default App
