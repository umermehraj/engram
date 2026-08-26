const FEATURES = [
  { name: 'Vector search', naive: true, mem0: true, zep: true, engram: true },
  { name: 'Knowledge graph', naive: false, mem0: 'partial', zep: true, engram: true },
  { name: 'Temporal versioning', naive: false, mem0: false, zep: 'partial', engram: true },
  { name: 'Multi-hop traversal', naive: false, mem0: false, zep: true, engram: true },
  { name: 'Multimodal (img/audio/PDF)', naive: false, mem0: false, zep: false, engram: true },
  { name: 'Fully local / embedded', naive: false, mem0: false, zep: false, engram: true },
  { name: 'Open source', naive: false, mem0: 'partial', zep: 'partial', engram: true },
]

function Cell({ value }: { value: boolean | string }) {
  if (value === true) return <span className="text-green">&#10003;</span>
  if (value === 'partial') return <span className="text-orange text-xs">partial</span>
  return <span className="text-gray-600">&mdash;</span>
}

export function ComparisonTable() {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-3 px-4 text-gray-400 font-medium" />
            <th className="py-3 px-4 text-gray-500 font-medium">Naive RAG</th>
            <th className="py-3 px-4 text-gray-500 font-medium">Mem0</th>
            <th className="py-3 px-4 text-gray-500 font-medium">Zep</th>
            <th className="py-3 px-4 text-accent font-semibold">Engram</th>
          </tr>
        </thead>
        <tbody>
          {FEATURES.map((f) => (
            <tr key={f.name} className="border-b border-border/50 hover:bg-surface-3/30 transition-colors">
              <td className="py-3 px-4 text-gray-300">{f.name}</td>
              <td className="py-3 px-4 text-center"><Cell value={f.naive} /></td>
              <td className="py-3 px-4 text-center"><Cell value={f.mem0} /></td>
              <td className="py-3 px-4 text-center"><Cell value={f.zep} /></td>
              <td className="py-3 px-4 text-center"><Cell value={f.engram} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
