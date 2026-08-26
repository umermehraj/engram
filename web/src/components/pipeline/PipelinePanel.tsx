import { memo, type ReactNode } from 'react'
import { motion } from 'framer-motion'

interface PipelinePanelProps {
  number: number
  title: string
  subtitle?: string
  children: ReactNode
  onVisible?: (n: number) => void
}

export const PipelinePanel = memo(function PipelinePanel({
  number,
  title,
  subtitle,
  children,
  onVisible,
}: PipelinePanelProps) {
  return (
    <motion.div
      className="min-h-screen flex flex-col justify-center py-20 px-4 md:px-8"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5 }}
      onViewportEnter={() => onVisible?.(number)}
    >
      <div className="max-w-4xl mx-auto w-full space-y-8">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent/20 border border-accent/40 text-accent text-sm font-bold">
              {number}
            </span>
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              Step {number} of 8
            </span>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-white">{title}</h2>
          {subtitle && <p className="text-gray-400 text-sm md:text-base max-w-2xl">{subtitle}</p>}
        </div>
        {children}
      </div>
    </motion.div>
  )
})
