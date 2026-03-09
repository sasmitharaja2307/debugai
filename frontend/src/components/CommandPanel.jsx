/**
 * POLYHEAL AI – Command Panel
 * Developer terminal input: run commands and view raw output.
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Terminal, Play, ChevronDown } from 'lucide-react'
import toast from 'react-hot-toast'
import { runCommand } from '../api/client'

const EXAMPLE_COMMANDS = [
  'python app.py',
  'java Main',
  'node app.js',
  'go run main.go',
  'gcc main.c -o main',
  'g++ main.cpp -o main',
]

export default function CommandPanel({ onReport, onRunningChange }) {
  const [command, setCommand]       = useState('')
  const [snippet, setSnippet]       = useState('')
  const [loading, setLoading]       = useState(false)
  const [rawOutput, setRawOutput]   = useState(null)

  const handleRun = async () => {
    if (!command.trim()) {
      toast.error('Enter a command to run.')
      return
    }
    setLoading(true)
    onRunningChange?.(true)
    setRawOutput(null)
    try {
      const { data } = await runCommand(command, snippet)
      setRawOutput(data)
      onReport?.(data)
      if (data.success) {
        toast.success('Command executed successfully!')
      } else {
        toast.error(`Errors detected – ${data.errors?.length ?? 0} issue(s) found.`)
      }
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
      onRunningChange?.(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Title */}
      <div className="flex items-center gap-2 mb-1">
        <Terminal size={18} className="text-brand-400" />
        <h2 className="font-semibold text-gray-100">Run Command</h2>
      </div>

      {/* Command input */}
      <div className="card flex flex-col gap-3">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-mono text-sm">$</span>
            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRun()}
              placeholder="python app.py"
              className="w-full bg-surface-900 border border-surface-600 rounded-lg pl-7 pr-4 py-2.5
                         text-sm font-mono text-gray-100 placeholder-gray-600
                         focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition"
            />
          </div>
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleRun}
            disabled={loading}
            className="btn-primary flex items-center gap-2 min-w-[100px] justify-center"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Play size={14} />
            )}
            {loading ? 'Running…' : 'Run'}
          </motion.button>
        </div>

        {/* Quick examples */}
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_COMMANDS.map((cmd) => (
            <button
              key={cmd}
              onClick={() => setCommand(cmd)}
              className="text-xs bg-surface-700 hover:bg-surface-600 border border-surface-600 text-gray-400 hover:text-gray-200 px-2.5 py-1 rounded-md font-mono transition-all"
            >
              {cmd}
            </button>
          ))}
        </div>

        {/* Optional code snippet */}
        <details className="group">
          <summary className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition select-none">
            <ChevronDown size={12} className="group-open:rotate-180 transition-transform" />
            Attach code snippet (optional – improves AI analysis)
          </summary>
          <textarea
            value={snippet}
            onChange={(e) => setSnippet(e.target.value)}
            placeholder="Paste your code here..."
            rows={6}
            className="mt-2 w-full bg-surface-900 border border-surface-600 rounded-lg p-3
                       text-xs font-mono text-gray-300 placeholder-gray-600
                       focus:outline-none focus:border-brand-500 resize-y"
          />
        </details>
      </div>

      {/* Raw output */}
      {rawOutput && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-gray-400 font-mono">Output – exit code: {rawOutput.run_result?.returncode}</span>
            <span className={`badge ${rawOutput.success ? 'badge-success' : 'badge-critical'}`}>
              {rawOutput.success ? '✓ Success' : '✗ Failed'}
            </span>
          </div>

          {rawOutput.run_result?.stdout && (
            <pre className="text-xs font-mono bg-surface-900 rounded-lg p-3 text-green-300 overflow-auto max-h-40 whitespace-pre-wrap">
              {rawOutput.run_result.stdout}
            </pre>
          )}
          {rawOutput.run_result?.stderr && (
            <pre className="mt-2 text-xs font-mono bg-surface-900 rounded-lg p-3 text-red-400 overflow-auto max-h-40 whitespace-pre-wrap">
              {rawOutput.run_result.stderr}
            </pre>
          )}
        </motion.div>
      )}
    </div>
  )
}
