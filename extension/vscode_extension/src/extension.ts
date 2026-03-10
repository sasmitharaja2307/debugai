/**
 * SELFHEAL AI – VS Code Extension
 * Monitors terminal output, surfaces AI solutions inside VS Code.
 */

import * as vscode from 'vscode'
import axios from 'axios'

let statusBarItem: vscode.StatusBarItem
let outputChannel: vscode.OutputChannel
let lastTerminalOutput = ''

// ── Helpers ────────────────────────────────────────────────────────────────

function getApiUrl(): string {
  const cfg = vscode.workspace.getConfiguration('selfheal')
  return cfg.get<string>('apiUrl', 'http://localhost:8000')
}

async function callApi<T>(path: string, method: 'GET' | 'POST', body?: object): Promise<T | null> {
  try {
    const url = `${getApiUrl()}${path}`
    const resp = method === 'POST'
      ? await axios.post(url, body, { timeout: 60_000 })
      : await axios.get(url, { timeout: 30_000 })
    return resp.data as T
  } catch (err: any) {
    outputChannel.appendLine(`[SelfHeal] API error: ${err.message}`)
    return null
  }
}

// ── Webview panel for solutions ─────────────────────────────────────────────

function buildSolutionsHtml(report: any): string {
  const errors = (report?.errors ?? [])
    .map((e: any) => `<li><b>${e.error_type}</b>: ${e.message} (${e.language})</li>`)
    .join('')

  const solutions = (report?.solutions ?? [])
    .map((s: any) => `
      <div class="solution">
        <h3>${s.index}. ${s.title}</h3>
        <p>${s.explanation}</p>
        <div class="metrics">
          <span>⏱ Time: <b>${s.time_complexity}</b></span>
          <span>💾 Space: <b>${s.space_complexity}</b></span>
          <span>⚡ Perf: <b>${s.performance_score}/10</b></span>
          <span>🔒 Sec: <b>${s.security_score}/100</b></span>
        </div>
        ${s.fix_command ? `<code>$ ${s.fix_command}</code>` : ''}
        ${s.code_patch ? `<pre>${s.code_patch}</pre>` : ''}
        <button onclick="applySolution(${s.index})">Apply Solution</button>
      </div>`)
    .join('')

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 16px; }
  h2 { color: #748eff; }
  .solution { background: var(--vscode-editor-inactiveSelectionBackground); border-radius: 8px; padding: 12px; margin: 10px 0; border: 1px solid #3237ce44; }
  .solution h3 { margin: 0 0 8px; color: #c084fc; }
  .metrics { display: flex; gap: 16px; margin: 8px 0; font-size: 12px; flex-wrap: wrap; }
  code { display: block; background: #0d0f1a; padding: 6px 10px; border-radius: 4px; margin: 6px 0; font-size: 12px; color: #748eff; }
  pre { background: #0d0f1a; padding: 10px; border-radius: 6px; font-size: 11px; overflow: auto; max-height: 200px; }
  button { background: #3d47e8; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; margin-top: 8px; font-size: 12px; }
  button:hover { background: #5265f5; }
  ul { margin: 0; padding-left: 20px; }
  .error-list { background: #1a0a0a; border: 1px solid #6b2020; border-radius: 6px; padding: 10px; margin: 10px 0; }
</style>
</head>
<body>
<h2>⚡ SELFHEAL AI – Debug Report</h2>
${errors ? `<div class="error-list"><b>Detected Errors:</b><ul>${errors}</ul></div>` : ''}
<h3>Generated Solutions</h3>
${solutions || '<p>No solutions generated.</p>'}
<script>
  const vscode = acquireVsCodeApi();
  const solutions = ${JSON.stringify(report?.solutions ?? [])};
  function applySolution(index) {
    const sol = solutions.find(s => s.index === index);
    if (sol) vscode.postMessage({ command: 'applySolution', solution: sol });
  }
</script>
</body>
</html>`
}

// ── Activation ───────────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext): void {
  outputChannel = vscode.window.createOutputChannel('SELFHEAL AI')
  outputChannel.appendLine('SELFHEAL AI extension activated.')

  // Status bar
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100)
  statusBarItem.command = 'selfheal.openDashboard'
  statusBarItem.text = '$(zap) SelfHeal'
  statusBarItem.tooltip = 'SELFHEAL AI – click to open dashboard'
  statusBarItem.show()
  context.subscriptions.push(statusBarItem)

  // ── Command: Run & Heal ──────────────────────────────────────────────────
  context.subscriptions.push(
    vscode.commands.registerCommand('selfheal.runCommand', async () => {
      const command = await vscode.window.showInputBox({
        prompt: 'Enter the command to run (e.g., python app.py)',
        placeHolder: 'python app.py',
      })
      if (!command) return

      statusBarItem.text = '$(sync~spin) SelfHeal: Analyzing…'
      const report = await callApi<any>('/run-command', 'POST', { command })
      statusBarItem.text = '$(zap) SelfHeal'

      if (!report) {
        vscode.window.showErrorMessage('SelfHeal: Could not reach the backend API.')
        return
      }

      const panel = vscode.window.createWebviewPanel(
        'selfheal.solutions',
        `SelfHeal – ${command}`,
        vscode.ViewColumn.Beside,
        { enableScripts: true }
      )
      panel.webview.html = buildSolutionsHtml(report)

      panel.webview.onDidReceiveMessage(async (msg) => {
        if (msg.command === 'applySolution') {
          const applyResult = await callApi<any>('/apply-solution', 'POST', { solution: msg.solution })
          if (applyResult?.status === 'applied') {
            vscode.window.showInformationMessage(`✓ Solution "${msg.solution.title}" applied!`)
          }
        }
      }, undefined, context.subscriptions)
    })
  )

  // ── Command: Analyze Selection ───────────────────────────────────────────
  context.subscriptions.push(
    vscode.commands.registerCommand('selfheal.analyzeSelection', async () => {
      const editor = vscode.window.activeTextEditor
      if (!editor) return
      const selection = editor.document.getText(editor.selection)
      if (!selection) return

      const langId = editor.document.languageId
      statusBarItem.text = '$(sync~spin) SelfHeal: Scanning…'
      const secResult = await callApi<any>('/security-check', 'POST', { code: selection })
      statusBarItem.text = '$(zap) SelfHeal'

      if (!secResult) return

      const msg = secResult.is_safe
        ? `✓ Code is safe (score: ${secResult.security_score}/100)`
        : `⚠ ${secResult.alerts?.length} security issue(s) found (score: ${secResult.security_score}/100)`
      vscode.window.showInformationMessage(msg, 'View Details').then((choice) => {
        if (choice === 'View Details') {
          outputChannel.appendLine(JSON.stringify(secResult, null, 2))
          outputChannel.show()
        }
      })
    })
  )

  // ── Command: Check Environment ───────────────────────────────────────────
  context.subscriptions.push(
    vscode.commands.registerCommand('selfheal.checkEnvironment', async () => {
      const result = await callApi<any>('/environment-status', 'GET')
      if (!result) return
      const criticals = result.critical_count ?? 0
      const total = result.issue_count ?? 0
      const msg = total === 0
        ? '✓ Environment is healthy!'
        : `Found ${total} issue(s) – ${criticals} critical`
      vscode.window.showWarningMessage(msg)
      outputChannel.appendLine(JSON.stringify(result, null, 2))
      outputChannel.show()
    })
  )

  // ── Command: Open Dashboard ──────────────────────────────────────────────
  context.subscriptions.push(
    vscode.commands.registerCommand('selfheal.openDashboard', () => {
      const cfg = vscode.workspace.getConfiguration('selfheal')
      const dashboardUrl = cfg.get<string>('apiUrl', 'http://localhost:5173')
      vscode.env.openExternal(vscode.Uri.parse(dashboardUrl))
    })
  )
}

export function deactivate(): void {
  outputChannel?.dispose()
  statusBarItem?.dispose()
}
