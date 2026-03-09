/**
 * POLYHEAL AI – Security Panel
 * Code security scanner + password strength validator.
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, Eye, EyeOff, AlertTriangle, CheckCircle2, Lock } from 'lucide-react'
import { securityCheck, passwordCheck } from '../api/client'
import toast from 'react-hot-toast'

const SEV_BADGE = {
  critical: 'badge-critical',
  high:     'badge-critical',
  medium:   'badge-warning',
  low:      'badge-info',
}

const STRENGTH_COLOR = {
  very_strong: 'text-green-400',
  strong:      'text-blue-400',
  moderate:    'text-yellow-400',
  weak:        'text-red-400',
}

export default function SecurityPanel() {
  const [code, setCode]           = useState('')
  const [scanResult, setScan]     = useState(null)
  const [scanning, setScanning]   = useState(false)

  const [password, setPassword]   = useState('')
  const [showPass, setShowPass]   = useState(false)
  const [passResult, setPassResult] = useState(null)

  const handleScan = async () => {
    if (!code.trim()) { toast.error('Paste code to scan.'); return }
    setScanning(true)
    try {
      const { data } = await securityCheck(code)
      setScan(data)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setScanning(false)
    }
  }

  const handlePasswordCheck = async () => {
    if (!password) return
    try {
      const { data } = await passwordCheck(password)
      setPassResult(data)
    } catch { /* ignore */ }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Shield size={18} className="text-brand-400" />
        <h2 className="font-semibold text-gray-100">Security Analysis</h2>
      </div>

      {/* Code scanner */}
      <div className="card space-y-3">
        <h3 className="text-sm font-semibold text-gray-300">Code Security Scanner</h3>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={7}
          placeholder="Paste code or a shell command to scan for vulnerabilities..."
          className="w-full bg-surface-900 border border-surface-600 rounded-lg p-3
                     text-xs font-mono text-gray-300 placeholder-gray-600
                     focus:outline-none focus:border-brand-500 resize-y"
        />
        <div className="flex justify-end">
          <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
            {scanning
              ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              : <Shield size={14} />}
            {scanning ? 'Scanning…' : 'Scan Code'}
          </button>
        </div>

        {scanResult && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            {/* Score */}
            <div className="flex items-center gap-4">
              <div className={`text-4xl font-bold score-ring w-14 h-14
                ${scanResult.security_score >= 80
                  ? 'border-green-500 text-green-400'
                  : scanResult.security_score >= 60
                    ? 'border-yellow-500 text-yellow-400'
                    : 'border-red-500 text-red-400'}`}>
                {scanResult.security_score}
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-200">Security Score</p>
                <p className={`text-xs mt-0.5 font-semibold ${scanResult.is_safe ? 'text-green-400' : 'text-red-400'}`}>
                  {scanResult.is_safe ? '✓ Code appears safe' : '✗ Security issues found'}
                </p>
              </div>
            </div>

            {/* Alerts */}
            {scanResult.alerts?.length > 0 && (
              <div className="space-y-2">
                {scanResult.alerts.map((a, i) => (
                  <div key={i} className="flex items-start gap-2 bg-red-900/20 border border-red-700/30 rounded-lg p-3">
                    <AlertTriangle size={13} className="text-red-400 mt-0.5 shrink-0" />
                    <div>
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={`badge ${SEV_BADGE[a.severity] ?? 'badge-warning'}`}>{a.severity}</span>
                        <span className="text-xs text-gray-500">{a.category}</span>
                      </div>
                      <p className="text-sm text-red-300">{a.description}</p>
                      <p className="text-xs text-gray-500 mt-0.5">💡 {a.recommendation}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {scanResult.alerts?.length === 0 && (
              <div className="flex items-center gap-2 text-green-400 text-sm">
                <CheckCircle2 size={15} /> No security issues detected.
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Password checker */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <Lock size={15} className="text-brand-400" />
          <h3 className="text-sm font-semibold text-gray-300">Password Strength Validator</h3>
        </div>
        <div className="relative">
          <input
            type={showPass ? 'text' : 'password'}
            value={password}
            onChange={(e) => { setPassword(e.target.value); handlePasswordCheck() }}
            placeholder="Enter a password to evaluate..."
            className="w-full bg-surface-900 border border-surface-600 rounded-lg px-3 py-2.5 pr-10
                       text-sm text-gray-200 placeholder-gray-600
                       focus:outline-none focus:border-brand-500 transition"
          />
          <button
            onClick={() => setShowPass(!showPass)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
          >
            {showPass ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>

        {passResult && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className={`font-semibold capitalize ${STRENGTH_COLOR[passResult.strength]}`}>
                {passResult.strength.replace('_', ' ')}
              </span>
              <span className="text-xs text-gray-500">Score {passResult.score}/6 · Length {passResult.length}</span>
            </div>
            {/* Criteria */}
            <div className="grid grid-cols-2 gap-1.5">
              {[
                ['Uppercase', passResult.has_uppercase],
                ['Lowercase', passResult.has_lowercase],
                ['Numbers',   passResult.has_digits],
                ['Special chars', passResult.has_special],
                ['12+ chars', passResult.length >= 12],
                ['16+ chars', passResult.length >= 16],
              ].map(([label, ok]) => (
                <div key={label} className={`flex items-center gap-2 text-xs px-2 py-1.5 rounded-md
                  ${ok ? 'bg-green-900/20 text-green-400' : 'bg-surface-700 text-gray-500'}`}>
                  {ok ? <CheckCircle2 size={11} /> : <span className="w-2.5 h-2.5 rounded-full border border-gray-600 ml-0.5" />}
                  {label}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
