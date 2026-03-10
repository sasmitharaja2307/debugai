/**
 * POLYHEAL AI – Environment Panel
 * Shows project environment health and dependency issues.
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { RefreshCw, CheckCircle2, AlertTriangle, Info, XCircle } from 'lucide-react'
import { getEnvironmentStatus } from '../api/client'
import toast from 'react-hot-toast'

const SEVERITY_MAP = {
  critical: { icon: XCircle,       cls: 'text-red-500',    bg: 'bg-red-50 border-red-200',       badge: 'badge-critical'  },
  warning:  { icon: AlertTriangle, cls: 'text-amber-500',  bg: 'bg-amber-50 border-amber-200',   badge: 'badge-warning'   },
  info:     { icon: Info,          cls: 'text-blue-500',   bg: 'bg-blue-50 border-blue-200',     badge: 'badge-info'      },
}

export default function EnvironmentPanel() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchStatus = async () => {
    setLoading(true)
    try {
      const { data: d } = await getEnvironmentStatus()
      setData(d)
    } catch (err) {
      toast.error('Failed to fetch environment status.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchStatus() }, [])

  const issues = data?.issues ?? []
  const critical = issues.filter((i) => i.severity === 'critical').length
  const warnings  = issues.filter((i) => i.severity === 'warning').length

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-slate-800">Environment Health</h2>
        <button
          onClick={fetchStatus}
          disabled={loading}
          className="btn-ghost flex items-center gap-2 text-sm"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total Issues',  value: issues.length, color: 'text-slate-800' },
          { label: 'Critical',      value: critical,       color: 'text-red-500'  },
          { label: 'Warnings',      value: warnings,       color: 'text-amber-500' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card text-center">
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-400 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Issue list */}
      <div className="card">
        {issues.length === 0 && !loading ? (
          <div className="flex items-center gap-2 text-green-600 py-4 justify-center">
            <CheckCircle2 size={18} />
            <span className="text-sm font-medium">All systems healthy!</span>
          </div>
        ) : (
          <div className="space-y-2">
            {issues.map((issue, i) => {
              const { icon: Icon, cls, bg, badge } = SEVERITY_MAP[issue.severity] ?? SEVERITY_MAP.info
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`flex items-start gap-3 border rounded-lg p-3 ${bg}`}
                >
                  <Icon size={15} className={`${cls} mt-0.5 shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`badge ${badge}`}>{issue.severity}</span>
                      <span className="badge badge-info">{issue.category}</span>
                    </div>
                    <p className="text-sm text-slate-700 mt-1">{issue.message}</p>
                    {issue.suggestion && (
                      <p className="text-xs text-slate-400 mt-1 font-mono">{issue.suggestion}</p>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
