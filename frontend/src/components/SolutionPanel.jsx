/**
 * POLYHEAL AI – Solution Panel
 * Displays multi-solution comparison cards with complexity metrics.
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Lightbulb, Zap, MemoryStick, Shield, Code2, 
  CheckCircle2, ChevronDown, Terminal, AlertTriangle
} from 'lucide-react'
import toast from 'react-hot-toast'
import { applySolution } from '../api/client'

const COMPLEXITY_COLOR = {
  'O(1)': 'text-green-600',
  'O(log n)': 'text-green-600',
  'O(1) avg': 'text-green-600',
  'O(n)': 'text-blue-600',
  'O(n log n)': 'text-blue-600',
  'O(n log n) avg': 'text-blue-600',
  'O(n²)': 'text-amber-600',
  'O(2^n)': 'text-red-600',
}
const getComplexityColor = (c) => COMPLEXITY_COLOR[c] ?? 'text-slate-500'

const SCORE_COLOR = (score) => {
  if (score >= 8) return 'border-green-500 text-green-600'
  if (score >= 5) return 'border-blue-500 text-blue-600'
  return 'border-red-500 text-red-600'
}

const SEC_COLOR = (score) => {
  if (score >= 80) return 'border-green-500 text-green-600'
  if (score >= 60) return 'border-amber-500 text-amber-600'
  return 'border-red-500 text-red-600'
}

function SolutionCard({ solution, isSelected, onSelect, onApply, applying }) {
  const [expanded, setExpanded] = useState(false)

  const badges = []
  if (solution.performance_score >= 8)  badges.push({ label: '⚡ Fastest',         cls: 'badge-success' })
  if (solution.security_score >= 90)    badges.push({ label: '🔒 Most Secure',     cls: 'badge-info'    })
  if (solution.difficulty === 'easy')   badges.push({ label: '✓ Easy Apply',        cls: 'badge-success' })

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`card cursor-pointer transition-all duration-200
        ${isSelected ? 'border-brand-500 ring-1 ring-brand-500/40 bg-brand-50' : 'hover:border-surface-500'}`}
      onClick={() => onSelect(solution.index)}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm
            ${isSelected ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
            {solution.index}
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 text-sm">{solution.title}</h3>
            <p className="text-xs text-slate-400 mt-0.5">{solution.difficulty} implementation</p>
          </div>
        </div>
        <div className="flex gap-1 flex-wrap justify-end">
          {badges.map((b) => (
            <span key={b.label} className={`badge ${b.cls}`}>{b.label}</span>
          ))}
        </div>
      </div>

      {/* Metrics row */}
      <div className="mt-4 grid grid-cols-4 gap-3">
        {/* Time complexity */}
        <div className="bg-slate-50 rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-400 mb-1">Time</p>
          <p className={`font-mono text-sm font-bold ${getComplexityColor(solution.time_complexity)}`}>
            {solution.time_complexity}
          </p>
        </div>
        {/* Space complexity */}
        <div className="bg-slate-50 rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-400 mb-1">Space</p>
          <p className={`font-mono text-sm font-bold ${getComplexityColor(solution.space_complexity)}`}>
            {solution.space_complexity}
          </p>
        </div>
        {/* Performance score */}
        <div className="bg-slate-50 rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-400 mb-1">Perf</p>
          <p className={`font-mono text-sm font-bold score-ring mx-auto w-7 h-7 text-xs
            ${SCORE_COLOR(solution.performance_score)}`}>
            {solution.performance_score}
          </p>
        </div>
        {/* Security score */}
        <div className="bg-slate-50 rounded-lg p-2.5 text-center">
          <p className="text-xs text-slate-400 mb-1">Security</p>
          <p className={`font-mono text-sm font-bold score-ring mx-auto w-7 h-7 text-xs
            ${SEC_COLOR(solution.security_score)}`}>
            {solution.security_score}
          </p>
        </div>
      </div>

      {/* Explanation */}
      <p className="mt-3 text-sm text-slate-600 leading-relaxed">{solution.explanation}</p>

      {/* Fix command */}
      {solution.fix_command && (
        <div className="mt-3 flex items-center gap-2 bg-brand-50 rounded-lg px-3 py-2">
          <Terminal size={12} className="text-brand-600 shrink-0" />
          <code className="text-xs font-mono text-brand-700">{solution.fix_command}</code>
        </div>
      )}

      {/* Expandable code patch */}
      {solution.code_patch && (
        <div className="mt-3">
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 transition"
          >
            <Code2 size={12} />
            {expanded ? 'Hide' : 'Show'} code patch
            <ChevronDown size={11} className={`transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </button>
          <AnimatePresence>
            {expanded && (
              <motion.pre
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-lg p-3 text-slate-700 overflow-auto max-h-64 whitespace-pre-wrap"
                onClick={(e) => e.stopPropagation()}
              >
                {solution.code_patch}
              </motion.pre>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Security alerts */}
      {solution.security_alerts?.length > 0 && (
        <div className="mt-3 space-y-1">
          {solution.security_alerts.map((alert, i) => (
            <div key={i} className="flex items-start gap-2 text-xs bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <AlertTriangle size={11} className="text-red-500 mt-0.5 shrink-0" />
              <span className="text-red-600">{alert.description}</span>
            </div>
          ))}
        </div>
      )}

      {/* Apply button (only on selected) */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 flex justify-end"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => onApply(solution)}
            disabled={applying}
            className="btn-primary flex items-center gap-2"
          >
            {applying
              ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              : <CheckCircle2 size={14} />}
            {applying ? 'Applying…' : 'Apply Solution'}
          </button>
        </motion.div>
      )}
    </motion.div>
  )
}

export default function SolutionPanel({ report }) {
  const [selected, setSelected]   = useState(null)
  const [applying, setApplying]   = useState(false)

  const errors    = report?.errors ?? []
  const solutions = report?.solutions ?? []
  const memorySuggestions = report?.memory_suggestions ?? []

  const handleApply = async (solution) => {
    setApplying(true)
    try {
      const { data } = await applySolution(solution)
      toast.success('Solution applied! Re-run your command to verify.')
      console.log('Apply result:', data)
    } catch (err) {
      toast.error('Failed to apply: ' + err.message)
    } finally {
      setApplying(false)
    }
  }

  if (!errors.length && !solutions.length) return null

  return (
    <div className="space-y-4">
      {/* Error summary */}
      {errors.length > 0 && (
        <div className="card border-red-300">
          <h2 className="font-semibold text-red-600 flex items-center gap-2 mb-3">
            <AlertTriangle size={16} />
            {errors.length} Error{errors.length > 1 ? 's' : ''} Detected
          </h2>
          {errors.map((err, i) => (
            <div key={i} className="flex items-start gap-3 bg-red-50 rounded-lg p-3 mb-2">
              <span className="badge badge-critical shrink-0">{err.language}</span>
              <div>
                <p className="text-sm font-mono text-red-600 font-semibold">{err.error_type}</p>
                <p className="text-xs text-slate-500 mt-0.5">{err.message}</p>
                {err.file && (
                  <p className="text-xs text-slate-400 mt-0.5 font-mono">
                    {err.file}{err.line ? `:${err.line}` : ''}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Memory suggestions */}
      {memorySuggestions.length > 0 && (
        <div className="card border-amber-300">
          <h3 className="text-xs font-semibold text-amber-600 mb-2 flex items-center gap-1.5">
            🧠 Previously successful fixes for similar errors
          </h3>
          {memorySuggestions.map((s, i) => (
            <div key={i} className="flex items-center justify-between bg-amber-50 rounded-lg px-3 py-2 mb-1">
              <span className="text-sm text-slate-700">{s.solution_title}</span>
              {s.fix_command && (
                <code className="text-xs font-mono text-amber-700 bg-amber-100 px-2 py-0.5 rounded">{s.fix_command}</code>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Solutions */}
      {solutions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb size={16} className="text-brand-600" />
            <h2 className="font-semibold text-slate-800">AI-Generated Solutions</h2>
            <span className="badge badge-info">{solutions.length} options</span>
          </div>
          <div className="space-y-3">
            {solutions.map((sol) => (
              <SolutionCard
                key={sol.index}
                solution={sol}
                isSelected={selected === sol.index}
                onSelect={setSelected}
                onApply={handleApply}
                applying={applying}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
