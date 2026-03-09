/**
 * POLYHEAL AI – Error History
 * Shows the self-learning debug memory with past error cases.
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Clock, RefreshCw, CheckCircle2, XCircle } from 'lucide-react'
import { getErrorHistory } from '../api/client'
import toast from 'react-hot-toast'

const LANG_COLORS = {
  python: 'bg-blue-900/60 text-blue-300 border-blue-700/50',
  java:   'bg-orange-900/60 text-orange-300 border-orange-700/50',
  javascript: 'bg-yellow-900/60 text-yellow-300 border-yellow-700/50',
  go:     'bg-cyan-900/60 text-cyan-300 border-cyan-700/50',
  c:      'bg-gray-700/60 text-gray-300 border-gray-600/50',
  cpp:    'bg-purple-900/60 text-purple-300 border-purple-700/50',
}

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return d.toLocaleString()
}

export default function ErrorHistory() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const { data } = await getErrorHistory()
      setHistory(data.history ?? [])
    } catch (err) {
      toast.error('Failed to fetch error history.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchHistory() }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock size={18} className="text-brand-400" />
          <h2 className="font-semibold text-gray-100">Debug Memory</h2>
          <span className="badge badge-info">{history.length} cases</span>
        </div>
        <button onClick={fetchHistory} disabled={loading} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {history.length === 0 && !loading ? (
        <div className="card text-center py-12">
          <Clock size={32} className="text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">No debug history yet. Run commands to build memory.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {history.map((c, i) => (
            <motion.div
              key={c.case_id ?? i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="card hover:border-surface-500 transition"
            >
              <div className="flex items-start gap-3">
                {c.was_successful
                  ? <CheckCircle2 size={15} className="text-green-400 mt-0.5 shrink-0" />
                  : <XCircle size={15} className="text-red-400 mt-0.5 shrink-0" />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className={`badge border ${LANG_COLORS[c.language] ?? 'badge-info'}`}>{c.language}</span>
                    <span className="text-xs font-mono text-gray-400">{c.error_type}</span>
                    <span className="text-xs text-gray-600 ml-auto">{formatDate(c.timestamp)}</span>
                  </div>
                  <p className="text-sm text-gray-300 truncate">{c.error_message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Applied: <span className="text-brand-400">{c.solution_title || '—'}</span>
                    {c.fix_command && (
                      <> · <code className="font-mono text-gray-400">{c.fix_command}</code></>
                    )}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
