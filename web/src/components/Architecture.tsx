export function Architecture() {
  return (
    <svg viewBox="0 0 800 520" className="w-full" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1" />
        </marker>
        <marker id="arrow-green" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#4ade80" />
        </marker>
        <marker id="arrow-orange" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#fb923c" />
        </marker>
        <linearGradient id="grad-accent" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0.05" />
        </linearGradient>
      </defs>

      {/* ── Input Sources (left) ── */}
      <g>
        <text x="30" y="100" fill="#9ca3af" fontSize="11" fontFamily="monospace">conversations</text>
        <text x="30" y="120" fill="#9ca3af" fontSize="11" fontFamily="monospace">documents</text>
        <text x="30" y="140" fill="#9ca3af" fontSize="11" fontFamily="monospace">code, images</text>
        <line x1="120" y1="120" x2="170" y2="120" stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrow)" />
      </g>

      {/* ── Ingestion Pipeline ── */}
      <g>
        <rect x="180" y="70" width="440" height="100" rx="12" fill="url(#grad-accent)" stroke="#6366f1" strokeWidth="1.5" strokeOpacity="0.4" />
        <text x="400" y="95" textAnchor="middle" fill="#e0e0e0" fontSize="14" fontWeight="600">Ingestion Pipeline</text>

        {/* Steps */}
        <rect x="200" y="110" width="80" height="32" rx="6" fill="#1a1a2e" stroke="#4f46e5" strokeWidth="1" />
        <text x="240" y="131" textAnchor="middle" fill="#a78bfa" fontSize="11">preprocess</text>

        <line x1="285" y1="126" x2="305" y2="126" stroke="#4f46e5" strokeWidth="1" markerEnd="url(#arrow)" />

        <rect x="310" y="110" width="80" height="32" rx="6" fill="#1a1a2e" stroke="#4f46e5" strokeWidth="1" />
        <text x="350" y="131" textAnchor="middle" fill="#a78bfa" fontSize="11">LLM extract</text>

        <line x1="395" y1="126" x2="415" y2="126" stroke="#4f46e5" strokeWidth="1" markerEnd="url(#arrow)" />

        <rect x="420" y="110" width="80" height="32" rx="6" fill="#1a1a2e" stroke="#4f46e5" strokeWidth="1" />
        <text x="460" y="131" textAnchor="middle" fill="#a78bfa" fontSize="11">resolve</text>

        <line x1="505" y1="126" x2="520" y2="126" stroke="#4f46e5" strokeWidth="1" markerEnd="url(#arrow)" />

        <rect x="525" y="110" width="80" height="32" rx="6" fill="#1a1a2e" stroke="#4f46e5" strokeWidth="1" />
        <text x="565" y="127" textAnchor="middle" fill="#fb923c" fontSize="10">temporal</text>
        <text x="565" y="139" textAnchor="middle" fill="#fb923c" fontSize="10">link</text>
      </g>

      {/* ── Dual Write arrows ── */}
      <line x1="330" y1="170" x2="280" y2="220" stroke="#4ade80" strokeWidth="2" markerEnd="url(#arrow-green)" />
      <line x1="470" y1="170" x2="520" y2="220" stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrow)" />

      {/* ── Storage Layer ── */}
      {/* Kuzu */}
      <g>
        <rect x="180" y="220" width="200" height="90" rx="12" fill="#0f0f23" stroke="#4ade80" strokeWidth="1.5" strokeOpacity="0.5" />
        <text x="280" y="248" textAnchor="middle" fill="#4ade80" fontSize="13" fontWeight="600">Kuzu Graph DB</text>
        <text x="280" y="268" textAnchor="middle" fill="#6b7280" fontSize="10">entities + edges</text>
        <text x="280" y="284" textAnchor="middle" fill="#6b7280" fontSize="10">temporal versioning</text>
        <text x="280" y="300" textAnchor="middle" fill="#4b5563" fontSize="9" fontFamily="monospace">valid_from / invalid_from</text>
      </g>

      {/* LanceDB */}
      <g>
        <rect x="420" y="220" width="200" height="90" rx="12" fill="#0f0f23" stroke="#6366f1" strokeWidth="1.5" strokeOpacity="0.5" />
        <text x="520" y="248" textAnchor="middle" fill="#6366f1" fontSize="13" fontWeight="600">LanceDB Vectors</text>
        <text x="520" y="268" textAnchor="middle" fill="#6b7280" fontSize="10">ANN similarity search</text>
        <text x="520" y="284" textAnchor="middle" fill="#6b7280" fontSize="10">entity embeddings</text>
        <text x="520" y="300" textAnchor="middle" fill="#4b5563" fontSize="9" fontFamily="monospace">384 / 1536 / 3072-dim</text>
      </g>

      {/* ── Retrieval arrows down ── */}
      <line x1="280" y1="310" x2="280" y2="350" stroke="#4ade80" strokeWidth="2" markerEnd="url(#arrow-green)" />
      <line x1="520" y1="310" x2="520" y2="350" stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrow)" />

      {/* ── Retrieval Engine ── */}
      <g>
        <rect x="140" y="350" width="520" height="140" rx="12" fill="url(#grad-accent)" stroke="#6366f1" strokeWidth="1.5" strokeOpacity="0.4" />
        <text x="400" y="378" textAnchor="middle" fill="#e0e0e0" fontSize="14" fontWeight="600">Retrieval Engine</text>

        {/* Three parallel search lanes */}
        <rect x="160" y="392" width="140" height="36" rx="6" fill="#1a1a2e" stroke="#6366f1" strokeWidth="1" />
        <text x="230" y="414" textAnchor="middle" fill="#6366f1" fontSize="11" fontWeight="500">vector search</text>

        <rect x="330" y="392" width="140" height="36" rx="6" fill="#1a1a2e" stroke="#4ade80" strokeWidth="1" />
        <text x="400" y="414" textAnchor="middle" fill="#4ade80" fontSize="11" fontWeight="500">graph traversal</text>

        <rect x="500" y="392" width="140" height="36" rx="6" fill="#1a1a2e" stroke="#fb923c" strokeWidth="1" />
        <text x="570" y="414" textAnchor="middle" fill="#fb923c" fontSize="11" fontWeight="500">temporal search</text>

        {/* Converge arrows */}
        <line x1="230" y1="428" x2="350" y2="452" stroke="#6366f1" strokeWidth="1.5" />
        <line x1="400" y1="428" x2="400" y2="452" stroke="#4ade80" strokeWidth="1.5" />
        <line x1="570" y1="428" x2="450" y2="452" stroke="#fb923c" strokeWidth="1.5" />

        {/* Fusion box */}
        <rect x="310" y="450" width="180" height="28" rx="6" fill="#1a1a2e" stroke="#a78bfa" strokeWidth="1.5" />
        <text x="400" y="469" textAnchor="middle" fill="#a78bfa" fontSize="11" fontWeight="600">Weighted RRF Fusion</text>
      </g>

      {/* ── Output arrow ── */}
      <line x1="400" y1="490" x2="400" y2="510" stroke="#a78bfa" strokeWidth="2" markerEnd="url(#arrow)" />
      <text x="400" y="520" textAnchor="middle" fill="#e0e0e0" fontSize="12" fontWeight="500" fontFamily="monospace">grounded context</text>

      {/* ── Query input (right) ── */}
      <g>
        <text x="700" y="380" fill="#9ca3af" fontSize="11" fontFamily="monospace">query</text>
        <line x1="690" y1="385" x2="645" y2="410" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="4 3" markerEnd="url(#arrow)" />
      </g>

      {/* ── "classify" label on query arrow ── */}
      <text x="680" y="400" fill="#a78bfa" fontSize="9" fontFamily="monospace">classify</text>
    </svg>
  )
}
