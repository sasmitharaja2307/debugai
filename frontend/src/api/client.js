/**
 * SELFHEAL AI – API Client
 * Centralised axios instance that talks to the FastAPI backend.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Error interceptor ──────────────────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'API request failed'
    console.error('[SelfHeal API]', msg)
    return Promise.reject(new Error(msg))
  }
)

// ── API helpers ─────────────────────────────────────────────────────────────

export const runCommand = (command, codeSnippet = '', searchSummary = '') =>
  api.post('/run-command', { command, code_snippet: codeSnippet, search_summary: searchSummary })

export const analyzeError = (errorData) =>
  api.post('/analyze-error', errorData)

export const getEnvironmentStatus = () =>
  api.get('/environment-status')

export const getErrorHistory = () =>
  api.get('/error-history')

export const applySolution = (solution, targetFile = null) =>
  api.post('/apply-solution', { solution, target_file: targetFile })

export const getCodeState = () =>
  api.get('/code-state')

export const securityCheck = (code) =>
  api.post('/security-check', { code })

export const passwordCheck = (password) =>
  api.post('/password-check', { password })

export default api
