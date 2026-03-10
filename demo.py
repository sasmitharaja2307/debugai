"""
SELFHEAL AI – Live Demo Script
Runs a buggy Python file, captures the error, calls the SELFHEAL API,
and prints the multi-solution analysis in the terminal.
"""

import json
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "http://localhost:8000"
DEMO_FILE = "examples/buggy_python.py"
SEP = "=" * 65


def color(text, code): return f"\033[{code}m{text}\033[0m"

RED    = lambda t: color(t, "91")
GREEN  = lambda t: color(t, "92")
YELLOW = lambda t: color(t, "93")
CYAN   = lambda t: color(t, "96")
BOLD   = lambda t: color(t, "1")
DIM    = lambda t: color(t, "2")


def call_api(path, method="GET", data=None):
    url = API_BASE + path
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        print(RED(f"  ❌ API unreachable: {e}"))
        print(YELLOW("  → Make sure backend is running: uvicorn backend.api_server:app --port 8000"))
        return None


def print_section(title):
    print(f"\n{SEP}")
    print(BOLD(CYAN(f"  {title}")))
    print(SEP)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 – Run the buggy file and show the raw error
# ─────────────────────────────────────────────────────────────────────────────
print_section("STEP 1 ▸ Running Buggy Python File")
print(f"  Command: {YELLOW('python examples/buggy_python.py')}\n")

result = subprocess.run(
    [sys.executable, DEMO_FILE],
    capture_output=True, text=True
)

if result.stdout:
    print(GREEN("  STDOUT:"))
    for line in result.stdout.strip().splitlines():
        print(f"    {line}")

if result.stderr:
    print(RED("  STDERR (Error Detected):"))
    for line in result.stderr.strip().splitlines():
        print(f"    {RED(line)}")

print(f"\n  Exit Code: {RED(str(result.returncode)) if result.returncode != 0 else GREEN('0')}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 – Send to SELFHEAL AI and get multi-solutions
# ─────────────────────────────────────────────────────────────────────────────
print_section("STEP 2 ▸ SELFHEAL AI – Detecting & Analyzing Error")

code_snippet = open(DEMO_FILE, encoding="utf-8").read()
payload = {
    "command": f"python {DEMO_FILE}",
    "code_snippet": code_snippet,
    "search_summary": "Python ZeroDivisionError when calling function with empty list"
}

print(f"  Sending to SELFHEAL API: {CYAN('POST /run-command')}  ...")
report = call_api("/run-command", "POST", payload)

if not report:
    sys.exit(1)

# Errors detected
errors = report.get("errors", [])
print(f"\n  {BOLD('Errors Detected:')} {RED(str(len(errors)))}\n")
for err in errors:
    print(f"    🔴 {BOLD(err['error_type'])} ({err['language']})")
    print(f"       {err['message']}")
    if err.get("file"):
        print(f"       {DIM('File: ' + err['file'] + (' :' + str(err['line']) if err.get('line') else ''))}")

# Environment issues
env_issues = report.get("environment_issues", [])
if env_issues:
    print(f"\n  {BOLD('Environment Issues:')} {YELLOW(str(len(env_issues)))}")
    for issue in env_issues[:3]:
        icon = "🔴" if issue["severity"] == "critical" else "🟡"
        print(f"    {icon} [{issue['severity'].upper()}] {issue['message']}")
        if issue.get("suggestion"):
            print(f"       💡 {DIM(issue['suggestion'])}")

# State diff
diff = report.get("state_diff")
if diff and diff.get("has_changes"):
    print(f"\n  {BOLD('Code State Changes Detected:')}")
    for f in diff.get("modified", []):
        print(f"    ✏  Modified: {YELLOW(f)}")
    for f in diff.get("added", []):
        print(f"    ➕ Added:    {GREEN(f)}")
    for f in diff.get("removed", []):
        print(f"    ➖ Removed:  {RED(f)}")

# Memory suggestions
memory = report.get("memory_suggestions", [])
if memory:
    print(f"\n  {BOLD('🧠 Memory – Previously Successful Fixes:')}")
    for m in memory:
        print(f"    • {m['solution_title']}  {DIM(m.get('fix_command',''))}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 – Show all solutions with complexity analysis
# ─────────────────────────────────────────────────────────────────────────────
print_section("STEP 3 ▸ AI-Generated Solutions with Complexity Analysis")

solutions = report.get("solutions", [])
if not solutions:
    print(YELLOW("  No LLM solutions (check OPENAI_API_KEY in .env). Showing offline fallback."))

for sol in solutions:
    perf = sol["performance_score"]
    perf_color = GREEN if perf >= 8 else (YELLOW if perf >= 5 else RED)
    sec = sol["security_score"]
    sec_color = GREEN if sec >= 80 else (YELLOW if sec >= 60 else RED)
    stars = "⭐" * min(perf // 2, 5)
    sol_title = f"Solution {sol['index']}: {sol['title']}"
    print(f"\n  ┌─ {BOLD(CYAN(sol_title))} {stars}")
    print(f"  │  Difficulty:    {YELLOW(sol['difficulty'])}")
    print(f"  │  Time Complex.: {CYAN(sol['time_complexity'])}")
    print(f"  │  Space Complex: {CYAN(sol['space_complexity'])}")
    print(f"  │  Perf Score:    {perf_color(str(perf) + '/10')}")
    print(f"  │  Sec Score:     {sec_color(str(sec) + '/100')}")
    print(f"  │")
    print(f"  │  {BOLD('Explanation:')}")
    for line in sol['explanation'].split('. '):
        if line.strip():
            print(f"  │    {line.strip()}.")
    if sol.get("fix_command"):
        print(f"  │")
        print(f"  │  {BOLD('Fix Command:')}  {GREEN('$ ' + sol['fix_command'])}")
    if sol.get("security_alerts"):
        print(f"  │  {RED('⚠ Security Alerts:')}")
        for alert in sol["security_alerts"]:
            print(f"  │    • [{alert['severity'].upper()}] {alert['description']}")
    print(f"  └{'─'*55}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 – Security scan of the buggy file
# ─────────────────────────────────────────────────────────────────────────────
print_section("STEP 4 ▸ Security Scanner")

sec_report = call_api("/security-check", "POST", {"code": code_snippet})
if sec_report:
    score = sec_report["security_score"]
    score_color = GREEN if score >= 80 else (YELLOW if score >= 60 else RED)
    print(f"  Security Score: {score_color(BOLD(str(score) + '/100'))}")
    print(f"  Status:         {'✅ Safe' if sec_report['is_safe'] else RED('❌ Issues Found')}\n")
    for alert in sec_report.get("alerts", []):
        print(f"  🚨 [{alert['severity'].upper()}] {BOLD(alert['category'])}")
        print(f"     {alert['description']}")
        print(f"     💡 {DIM(alert['recommendation'])}\n")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 – Environment Status
# ─────────────────────────────────────────────────────────────────────────────
print_section("STEP 5 ▸ Environment Health Check")

env_status = call_api("/environment-status", "GET")
if env_status:
    print(f"  Total Issues: {env_status['issue_count']}")
    print(f"  Critical:     {RED(str(env_status['critical_count']))}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print_section("DEMO COMPLETE ✅")
print(f"  {GREEN('✓')} Error detected and classified")
print(f"  {GREEN('✓')} {len(solutions)} solution(s) generated with complexity analysis")
print(f"  {GREEN('✓')} Security scan complete")
print(f"  {GREEN('✓')} Environment analyzed")
print(f"\n  {BOLD('Open the dashboard for visual results:')}")
print(f"  {CYAN('http://localhost:5173')}")
print(f"\n  {BOLD('View full API docs:')}")
print(f"  {CYAN('http://localhost:8000/docs')}\n")
