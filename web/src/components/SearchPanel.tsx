import { useState } from 'react'

const SUGGESTIONS = [
  'What backend framework are we using?',
  'What does Engram depend on?',
  "What are Saalik's preferences?",
  'When did we switch from Django?',
  'How does retrieval work?',
]

export function SearchPanel() {
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState(false)

  function handleSearch(q: string) {
    const text = q || query
    if (!text.trim()) return
    setQuery(text)
    setSubmitted(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setSubmitted(false) }}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(query) }}
          placeholder="Ask a question about the knowledge graph..."
          className="flex-1 px-4 py-3 rounded-xl bg-surface-2 border border-border text-gray-100 placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
        />
        <button
          onClick={() => handleSearch(query)}
          disabled={!query.trim()}
          className="px-6 py-3 rounded-xl bg-accent hover:bg-accent-dim text-white font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Search
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSearch(s)}
            className="px-3 py-1.5 text-sm rounded-lg bg-surface-3 border border-border text-gray-400 hover:text-gray-200 hover:border-accent/50 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {submitted && (
        <div className="p-5 rounded-xl bg-surface-2 border border-border text-sm text-gray-400 space-y-2">
          <p className="text-gray-300 font-medium">Live retrieval requires a running Engram instance.</p>
          <p>
            Clone the repo and run <code className="text-xs bg-surface-3 px-1.5 py-0.5 rounded text-accent">engram serve</code> to try
            hybrid vector + graph + temporal search against your own data.
          </p>
          <a
            href="https://github.com/Kaboom2025/engram"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-accent hover:underline"
          >
            View on GitHub →
          </a>
        </div>
      )}
    </div>
  )
}
