import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
import { 
  Bug, Activity, Shield, Clock, Terminal,
  ChevronRight, Zap, Code2, Database
} from 'lucide-react'

import CommandPanel   from './components/CommandPanel'
import SolutionPanel  from './components/SolutionPanel'
import EnvironmentPanel from './components/EnvironmentPanel'
import ErrorHistory   from './components/ErrorHistory'
import SecurityPanel  from './components/SecurityPanel'
import CodeStateDiff  from './components/CodeStateDiff'

const NAV_ITEMS = [
  { id: 'terminal',    label: 'Terminal',     icon: Terminal  },
  { id: 'environment', label: 'Environment',  icon: Activity  },
  { id: 'security',    label: 'Security',     icon: Shield    },
  { id: 'history',     label: 'Error History',icon: Clock     },
  { id: 'state',       label: 'Code State',   icon: Database  },
]

export default function App() {
  const [activeTab, setActiveTab]   = useState('terminal')
  const [report, setReport]         = useState(null)
  const [isRunning, setIsRunning]   = useState(false)

  return (
    <div className="min-h-screen bg-surface-900 flex flex-col">
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#ffffff', color: '#1e293b', border: '1px solid #e2e8f0' },
        }}
      />

      {/* ── Header ── */}
      <header className="border-b border-surface-600 bg-white/90 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/30">
              <Zap size={18} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg gradient-text leading-none">POLYHEAL AI</h1>
              <p className="text-xs text-slate-400 leading-none mt-0.5">Self-Healing Developer Agent</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isRunning && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-2 text-xs text-brand-600 bg-brand-50 px-3 py-1.5 rounded-full border border-brand-200"
              >
                <span className="w-1.5 h-1.5 bg-brand-600 rounded-full animate-pulse" />
                Analyzing…
              </motion.div>
            )}
            <span className="badge badge-success">v1.0</span>
          </div>
        </div>
      </header>

      {/* ── Layout ── */}
      <div className="flex flex-1 max-w-7xl mx-auto w-full px-6 py-6 gap-6">

        {/* Sidebar nav */}
        <nav className="w-48 shrink-0 flex flex-col gap-1">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                ${activeTab === id
                  ? 'bg-brand-50 text-brand-600 border border-brand-200'
                  : 'text-slate-500 hover:bg-surface-700 hover:text-slate-700'}`}
            >
              <Icon size={15} />
              {label}
              {activeTab === id && (
                <ChevronRight size={12} className="ml-auto text-brand-600" />
              )}
            </button>
          ))}
        </nav>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.18 }}
            >
              {activeTab === 'terminal' && (
                <div className="space-y-6">
                  <CommandPanel
                    onReport={setReport}
                    onRunningChange={setIsRunning}
                  />
                  {report && (
                    <SolutionPanel report={report} />
                  )}
                </div>
              )}
              {activeTab === 'environment' && <EnvironmentPanel />}
              {activeTab === 'security'    && <SecurityPanel />}
              {activeTab === 'history'     && <ErrorHistory />}
              {activeTab === 'state'       && <CodeStateDiff />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
