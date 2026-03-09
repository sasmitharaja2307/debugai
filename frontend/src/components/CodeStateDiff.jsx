/**
 * POLYHEAL AI – Code State Diff Viewer
 * Shows time-travel snapshots and file-level diffs.
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Database, RefreshCw, Plus, Minus, Edit3, CheckCircle2 } from 'lucide-react'
import { getCodeState } from '../api/client'
import toast from 'react-hot-toast'

function formatDate(ts) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleString()
}

function DiffRow({ file, type }) {
  const icons = {
    added:    { icon: Plus,   cls: 'text-green-400',  bg: 'bg-green-900/20 border-green-700/30' },
    removed:  { icon: Minus,  cls: 'text-red-400',    bg: 'bg-red-900/20 border-red-700/30'     },
    modified: { icon: Edit3,  cls: 'text-yellow-400', bg: 'bg-yellow-900/20 border-yellow-700/30' },
  }
  const { icon: Icon, cls, bg } = icons[type] ?? icons.modified
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono ${bg}`}>
      <Icon size={11} className={cls} />
      <span className="text-gray-300">{file}</span>
      <span className={`ml-auto uppercase text-xxs font-semibold ${cls}`}>{type}</span>
    </div>
  )
}

export default function CodeStateDiff() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchState = async () => {
    setLoading(true)
    try {
      const { data: d } = await getCodeState()
      setData(d)
    } catch (err) {
      toast.error('Failed to fetch code state.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchState() }, [])

  const history = data?.history ?? []
  const lastGood = data?.last_successful

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database size={18} className="text-brand-400" />
          <h2 className="font-semibold text-gray-100">Code State Tracker</h2>
          <span className="badge badge-info">{history.length} snapshots</span>
        </div>
        <button onClick={fetchState} disabled={loading} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Last successful run */}
      {lastGood && (
        <div className="card border-green-700/40">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 size={14} className="text-green-400" />
            <span className="text-sm font-semibold text-green-400">Last Successful Run</span>
          </div>
          <p className="text-xs text-gray-500 font-mono">{lastGood.command}</p>
          <p className="text-xs text-gray-600 mt-0.5">{formatDate(lastGood.timestamp)}</p>
          <p className="text-xs text-gray-500 mt-1">{lastGood.file_count} files tracked</p>
        </div>
      )}

      {/* Snapshot history */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Snapshot History</h3>
        {history.length === 0 ? (
          <p className="text-center text-gray-500 text-sm py-6">No snapshots yet. Run a command to start tracking.</p>
        ) : (
          <div className="space-y-2">
            {[...history].reverse().map((snap, i) => (
              <motion.div
                key={snap.run_id ?? i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="flex items-center gap-3 bg-surface-700/40 rounded-lg px-3 py-2.5"
              >
                <span className={`w-2 h-2 rounded-full shrink-0 ${snap.success ? 'bg-green-400' : 'bg-red-400'}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-mono text-gray-300 truncate">{snap.command}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{formatDate(snap.timestamp)}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs text-gray-500">{snap.file_count} files</p>
                  <span className={`badge ${snap.success ? 'badge-success' : 'badge-critical'} text-xs`}>
                    {snap.success ? 'OK' : 'FAIL'}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
