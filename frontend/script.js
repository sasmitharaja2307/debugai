// ── Config ─────────────────────────────────────────────────────
// Use the same host that served this page (works on localhost:5000 and any host)
const API = `${window.location.origin}/api`;

// ── State ──────────────────────────────────────────────────────
let _lastOriginal  = "";
let _lastOptimized = "";
let _showingDiff   = false;

// ── Examples per language ─────────────────────────────────────
const EXAMPLES = {
  python: `# Buggy Python — try Optimize!
print("Testing AI Code Optimizer")

numbers = [5, 2, 9, 1]
numbers.sort()

# Typo: 'nombres' is not defined
print("Sorted:", nombres)

# Hardcoded secret (security issue)
API_KEY = "sk-hardcoded-abc123"

# O(n²) bubble sort — Complexity will flag this
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr`,

  javascript: `// Buggy JS — try Optimize!
var userName = "Alice";   // should use const/let

function greet() {
  console.log("Hello " + usrName);  // typo: usrName
}

// == instead of ===
if (userName == 1) {
  console.log("admin");
}

// Missing try/catch on fetch
function getData(url) {
  return fetch(url).then(r => r.json());
}`,

  java: `// Java example
import java.util.*;

public class Main {
  public static void main(String[] args) {
    String result = "";
    for (int i = 0; i < 1000; i++) {
      result += i;  // Performance issue!
    }
    System.out.println(result);  // Should use logger
  }
}`,

  go: `package main

import "fmt"

func divide(a, b int) int {
    return a / b  // panic if b == 0
}

func main() {
    fmt.Println(divide(10, 0))
    panic("something went wrong")  // bad practice
}`,
};

// ── DOM Helpers ────────────────────────────────────────────────
const $ = id => document.getElementById(id);

function getCode()  { return $("input-code").value; }
function getLang()  { return $("language").value; }

function showLoader(msg = "Processing…") {
  $("loader").classList.remove("hidden");
  $("loader-text").textContent = msg;
}
function hideLoader() { $("loader").classList.add("hidden"); }

function setOutput(html, title = "✅ Output") {
  $("output-area").innerHTML = html;
  $("output-title").textContent = title;
}

function clearCards() { $("cards-area").innerHTML = ""; }

function escHtml(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── Line Numbers ───────────────────────────────────────────────
function updateLineNumbers() {
  const code  = getCode();
  const lines = code.split("\n").length;
  const nums  = Array.from({length: lines}, (_, i) => i + 1).join("\n");
  $("line-numbers").textContent = nums;
  $("line-count").textContent   = `${lines} line${lines !== 1 ? "s" : ""}`;
  $("char-count").textContent   = `${code.length} chars`;
}

function syncScroll() {
  $("line-numbers").scrollTop = $("input-code").scrollTop;
}

function onCodeInput() {
  updateLineNumbers();
  _showingDiff = false;
  $("btn-diff").style.display = "none";
}

function handleTab(e) {
  if (e.key !== "Tab") return;
  e.preventDefault();
  const ta    = $("input-code");
  const start = ta.selectionStart;
  const end   = ta.selectionEnd;
  ta.value    = ta.value.substring(0, start) + "    " + ta.value.substring(end);
  ta.selectionStart = ta.selectionEnd = start + 4;
  onCodeInput();
}

function onLangChange() {
  clearCards();
  setOutput('<span class="placeholder">Click Optimize, Explain, Complexity or Run…</span>');
}

// ── Example Loader ─────────────────────────────────────────────
function pasteExample() {
  const lang = getLang();
  const code = EXAMPLES[lang] || EXAMPLES.python;
  $("input-code").value = code;
  onCodeInput();
  showToast("Example loaded!");
}

// ── Copy ───────────────────────────────────────────────────────
function copyInput() {
  copyText(getCode(), "Code copied!");
}

function copyOutput() {
  copyText($("output-area").innerText, "Output copied!");
}

function copyText(text, msg = "Copied!") {
  if (!text.trim()) { showToast("Nothing to copy", true); return; }
  navigator.clipboard.writeText(text)
    .then(() => showToast(msg))
    .catch(() => {
      // Fallback for older browsers / HTTP
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity  = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      showToast(msg);
    });
}

// ── Toast ──────────────────────────────────────────────────────
function showToast(msg, isError = false) {
  const t = document.createElement("div");
  t.textContent = msg;
  Object.assign(t.style, {
    position:"fixed", bottom:"24px", right:"24px",
    background: isError ? "var(--red)" : "var(--green)",
    color:"#0d1117", padding:"9px 18px", borderRadius:"8px",
    fontWeight:"600", fontSize:"0.85rem", zIndex:"9999",
    boxShadow:"0 4px 20px rgba(0,0,0,0.4)", pointerEvents:"none",
  });
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2800);
}

// ── API Call ───────────────────────────────────────────────────
async function callAPI(endpoint, payload) {
  const res = await fetch(`${API}/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);
  return data;
}

// ── Highlight Code ─────────────────────────────────────────────
function highlightCode(code, lang) {
  const prismLang = {
    python:"python", javascript:"javascript", typescript:"javascript",
    java:"java", go:"go", cpp:"cpp", c:"c", ruby:"ruby", php:"php",
  }[lang] || "none";

  if (window.Prism && Prism.languages[prismLang]) {
    return `<code class="language-${prismLang}">${Prism.highlight(escHtml(code), Prism.languages[prismLang], prismLang)}</code>`;
  }
  return `<code>${escHtml(code)}</code>`;
}

// ── Diff View ──────────────────────────────────────────────────
function buildDiff(original, optimized) {
  const orig = original.split("\n");
  const opti = optimized.split("\n");
  let html   = '<span class="diff-info">← removed (red)  ·  + added (green)</span>';

  const maxLen = Math.max(orig.length, opti.length);
  for (let i = 0; i < maxLen; i++) {
    const a = orig[i] ?? null;
    const b = opti[i] ?? null;
    if (a === b) {
      html += `<span>${escHtml(a ?? "")}</span>\n`;
    } else {
      if (a !== null) html += `<span class="diff-remove">${escHtml(a)}</span>\n`;
      if (b !== null) html += `<span class="diff-add">${escHtml(b)}</span>\n`;
    }
  }
  return `<pre style="font-family:var(--mono);font-size:0.85rem;line-height:1.6">${html}</pre>`;
}

function toggleDiff() {
  if (_showingDiff) {
    setOutput(`<pre style="margin:0">${highlightCode(_lastOptimized, getLang())}</pre>`, "✅ Optimized");
    $("btn-diff").textContent = "⇄ Diff";
  } else {
    setOutput(buildDiff(_lastOriginal, _lastOptimized), "⇄ Diff View");
    $("btn-diff").textContent = "← Code";
  }
  _showingDiff = !_showingDiff;
}

// ── Card Builders ──────────────────────────────────────────────
function makeCard(title, contentHTML, colorClass = "") {
  const card = document.createElement("div");
  card.className = `card ${colorClass}`;
  card.innerHTML = `<div class="card-title">${title}</div>${contentHTML}`;
  $("cards-area").appendChild(card);
}

function makeBigCard(title, value, colorClass = "") {
  makeCard(title, `<div class="big-value">${escHtml(String(value))}</div>`, colorClass);
}

function makeListCard(title, items, colorClass = "") {
  if (!items?.length) return;
  const li = items.map(i => {
    const cls = i.startsWith("[BUG]") || i.startsWith("[SYNTAX") ? "bug"
              : i.startsWith("[SECURITY]") ? "sec"
              : i.startsWith("⚠") ? "warn" : "";
    return `<li class="${cls}">${escHtml(i)}</li>`;
  }).join("");
  makeCard(title, `<ul>${li}</ul>`, colorClass);
}

// ── Mode Badge ─────────────────────────────────────────────────
function setMode(mode) {
  const el = $("mode-badge");
  if (mode === "ai") {
    el.textContent = "🤖 AI Mode";
    el.className   = "badge-mode ai";
  } else {
    el.textContent = "⚙ Offline Mode";
    el.className   = "badge-mode offline";
  }
}

// ── Error Display ──────────────────────────────────────────────
function showError(err) {
  hideLoader();
  const msg = err.message || String(err);
  const isConn = msg.includes("fetch") || msg.includes("Failed to fetch") || msg.includes("NetworkError");
  setOutput(
    `<div style="color:var(--red);font-family:var(--mono);font-size:0.85rem;line-height:1.8">
      <strong>Error:</strong> ${escHtml(msg)}
      ${isConn ? `\n\n<span style="color:var(--muted)">Backend not running?\nStart it with:\n  python backend/app.py</span>` : ""}
    </div>`,
    "❌ Error"
  );
}

// ── OPTIMIZE ───────────────────────────────────────────────────
async function runOptimize() {
  const code = getCode();
  if (!code.trim()) { showToast("Paste some code first!", true); return; }
  showLoader("Optimizing your code…");
  clearCards();

  try {
    const data = await callAPI("optimize", { code, language: getLang() });
    hideLoader();
    setMode(data.mode);

    const optimized = data.optimized_code || code;
    _lastOriginal  = code;
    _lastOptimized = optimized;

    // Show highlighted output
    setOutput(`<pre style="margin:0">${highlightCode(optimized, getLang())}</pre>`, "✅ Optimized");

    // Show diff button only if something changed
    const changed = optimized.trim() !== code.trim();
    $("btn-diff").style.display = changed ? "inline-block" : "none";
    $("btn-diff").textContent   = "⇄ Diff";
    _showingDiff = false;

    // Cards
    makeListCard("🔧 Improvements / Issues", data.improvements);

    if (data.performance_gain) {
      makeBigCard("🚀 Performance", data.performance_gain, changed ? "green" : "");
    }

    if (data.readability_score !== undefined) {
      const s   = data.readability_score;
      const cls = s >= 8 ? "green" : s >= 5 ? "yellow" : "red";
      makeBigCard("📖 Readability", `${s}<span style="font-size:1rem;color:var(--muted)">/10</span>`, cls);
    }

    if (data.issue_count !== undefined) {
      makeBigCard("🐛 Issues Found", data.issue_count, data.issue_count > 0 ? "red" : "green");
    }

    makeBigCard("Engine", data.mode === "ai" ? "🤖 AI (GPT)" : "⚙ Offline AST");

  } catch (err) { showError(err); }
}

// ── EXPLAIN ────────────────────────────────────────────────────
async function runExplain() {
  const code = getCode();
  if (!code.trim()) { showToast("Paste some code first!", true); return; }
  showLoader("Explaining your code…");
  clearCards();

  try {
    const data = await callAPI("explain", { code, language: getLang() });
    hideLoader();
    setMode(data.mode);

    setOutput(
      `<p style="line-height:1.9;font-family:inherit;font-size:0.92rem;color:var(--text)">${escHtml(data.explanation || "")}</p>`,
      "🔍 Explanation"
    );

    makeListCard("📚 Key Concepts",      data.key_concepts);
    makeListCard("⚠️ Potential Issues",  data.potential_issues, "yellow");
    makeListCard("💡 Suggestions",       data.suggestions,      "green");

  } catch (err) { showError(err); }
}

// ── COMPLEXITY ─────────────────────────────────────────────────
async function runComplexity() {
  const code = getCode();
  if (!code.trim()) { showToast("Paste some code first!", true); return; }
  showLoader("Analysing complexity…");
  clearCards();

  try {
    const data = await callAPI("complexity", { code, language: getLang() });
    hideLoader();
    setMode(data.mode);

    setOutput(
      `<p style="line-height:1.9;font-family:inherit;font-size:0.92rem;color:var(--text)">${escHtml(data.summary || "")}</p>`,
      "📊 Complexity"
    );

    const tc  = data.time_complexity || "?";
    const bad = tc.includes("n²") || tc.includes("n³") || tc.includes("2ⁿ");
    makeBigCard("⏱ Time Complexity",  tc, bad ? "red" : "green");
    makeBigCard("💾 Space Complexity", data.space_complexity || "?");

    if (data.bottleneck) {
      makeCard("🐢 Bottleneck",
        `<p style="color:var(--yellow);font-size:0.88rem;line-height:1.6">${escHtml(data.bottleneck)}</p>`,
        "yellow"
      );
    }

  } catch (err) { showError(err); }
}

// ── RUN ────────────────────────────────────────────────────────
async function runCode() {
  const code = getCode();
  if (!code.trim()) { showToast("Paste some code first!", true); return; }

  showLoader("Running your code…");
  $("run-panel").classList.add("hidden");
  $("run-stderr").classList.add("hidden");

  try {
    const data = await callAPI("run", { code, language: getLang() });
    hideLoader();

    // Show run panel
    $("run-panel").classList.remove("hidden");

    const stdout = data.stdout || "";
    const stderr = data.stderr || "";
    const exit   = data.exit_code ?? 0;
    const ms     = data.runtime_ms ?? 0;

    $("run-stdout").textContent  = stdout || "(no output)";
    $("run-meta").textContent    = `exit: ${exit}  ·  ${ms}ms`;
    $("run-meta").style.color    = exit === 0 ? "var(--green)" : "var(--red)";

    if (stderr) {
      $("run-stderr").textContent = stderr;
      $("run-stderr").classList.remove("hidden");
    }

    // If there was an error, also show in output panel with suggestions
    if (exit !== 0 && stderr) {
      setOutput(
        `<div style="color:var(--red);font-family:var(--mono);font-size:0.84rem;line-height:1.8">${escHtml(stderr)}</div>\n` +
        `<div style="color:var(--muted);font-size:0.82rem;margin-top:12px">💡 Try clicking <strong>⚡ Optimize</strong> to auto-detect and fix these errors.</div>`,
        "❌ Runtime Error"
      );
    } else {
      setOutput(
        `<div style="color:var(--green);font-family:var(--mono);font-size:0.84rem">✅ Ran successfully in ${ms}ms</div>`,
        "▶ Run Result"
      );
    }

  } catch (err) { showError(err); }
}

function closeRunPanel() {
  $("run-panel").classList.add("hidden");
}

// ── Clear ──────────────────────────────────────────────────────
function clearAll() {
  $("input-code").value = "";
  setOutput('<span class="placeholder">Click Optimize, Explain, Complexity or Run…</span>');
  clearCards();
  $("run-panel").classList.add("hidden");
  $("btn-diff").style.display = "none";
  _lastOriginal = _lastOptimized = "";
  _showingDiff  = false;
  updateLineNumbers();
}

// ── Backend Health Check ───────────────────────────────────────
async function checkHealth() {
  const dot = $("status-dot");
  try {
    const r = await fetch(`${API}/health`, { cache: "no-store" });
    if (r.ok) {
      dot.className = "status-dot online";
      dot.title     = "Backend online";
    } else {
      dot.className = "status-dot offline";
    }
  } catch {
    dot.className = "status-dot offline";
    dot.title     = "Backend offline";
  }
}

// ── Init ───────────────────────────────────────────────────────
updateLineNumbers();
checkHealth();
setInterval(checkHealth, 15000);  // re-check every 15s
