import type { ReactNode } from 'react'

interface SectionProps {
  id?: string
  title: string
  subtitle?: string
  children: ReactNode
}

export function Section({ id, title, subtitle, children }: SectionProps) {
  return (
    <section id={id} className="py-16 px-6 md:px-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h2 className="text-3xl font-bold text-white">{title}</h2>
          {subtitle && <p className="mt-2 text-gray-400">{subtitle}</p>}
        </div>
        {children}
      </div>
    </section>
  )
}
