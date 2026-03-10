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
  python: 'bg-blue-100 text-blue-700 border-blue-300',
  java:   'bg-orange-100 text-orange-700 border-orange-300',
  javascript: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  go:     'bg-cyan-100 text-cyan-700 border-cyan-300',
  c:      'bg-slate-100 text-slate-700 border-slate-300',
  cpp:    'bg-purple-100 text-purple-700 border-purple-300',
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
          <Clock size={18} className="text-brand-600" />
          <h2 className="font-semibold text-slate-800">Debug Memory</h2>
          <span className="badge badge-info">{history.length} cases</span>
        </div>
        <button onClick={fetchHistory} disabled={loading} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {history.length === 0 && !loading ? (
        <div className="card text-center py-12">
          <Clock size={32} className="text-slate-300 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">No debug history yet. Run commands to build memory.</p>
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
                  ? <CheckCircle2 size={15} className="text-green-600 mt-0.5 shrink-0" />
                  : <XCircle size={15} className="text-red-500 mt-0.5 shrink-0" />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className={`badge border ${LANG_COLORS[c.language] ?? 'badge-info'}`}>{c.language}</span>
                    <span className="text-xs font-mono text-slate-500">{c.error_type}</span>
                    <span className="text-xs text-slate-400 ml-auto">{formatDate(c.timestamp)}</span>
                  </div>
                  <p className="text-sm text-slate-700 truncate">{c.error_message}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Applied: <span className="text-brand-600">{c.solution_title || '—'}</span>
                    {c.fix_command && (
                      <> · <code className="font-mono text-slate-500">{c.fix_command}</code></>
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
