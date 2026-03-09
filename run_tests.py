"""
POLYHEAL AI – Quick Test Runner
Run:  python run_tests.py
"""

import subprocess, sys, json, textwrap, pathlib, os

PYTHON = sys.executable
BASE   = pathlib.Path(__file__).parent
EXAMPLES = BASE / "examples"

SEP  = "=" * 65
DASH = "-" * 65

def section(title: str):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

def run(cmd: list[str]) -> tuple[str, str, int]:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    return r.stdout, r.stderr, r.returncode

def run_command_api(command: str, code_snippet: str = "") -> dict:
    """Call POST /run-command — full POLYHEAL pipeline: run → detect → solutions."""
    try:
        import requests
        payload = {
            "command": command,
            "code_snippet": code_snippet,
        }
        r = requests.post("http://localhost:8000/run-command", json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def security_check(code: str) -> dict:
    try:
        import requests
        r = requests.post(
            "http://localhost:8000/security-check",
            json={"code": code},
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}

# ──────────────────────────────────────────────────────────────
# TEST 1 – Run the buggy Python file and let POLYHEAL analyse it
# ──────────────────────────────────────────────────────────────
section("TEST 1 · Buggy Python  →  examples/test_python.py")

py_code = (EXAMPLES / "test_python.py").read_text()
stdout, stderr, code = run([PYTHON, str(EXAMPLES / "test_python.py")])

error_output = stderr or stdout
print(f"\n[Exit code: {code}]")
print("\n[RUNTIME ERROR CAPTURED]")
print(textwrap.indent(error_output.strip()[:600], "  "))

print("\n[SENDING TO POLYHEAL BACKEND…]")
result = run_command_api(f"{PYTHON} {EXAMPLES / 'test_python.py'}", py_code)

if "error" in result:
    print(f"  ⚠️  {result['error']}")
    print(f"  Start the backend:  {PYTHON} -m uvicorn backend.api_server:app --reload --port 8000")
else:
    errs = result.get("detected_errors", [])
    solutions = result.get("solutions", [])
    print(f"\n  Errors detected  : {len(errs)}")
    for e in errs[:3]:
        print(f"    • [{e.get('severity','?').upper()}] {e.get('type','?')} on line {e.get('line','?')} — {e.get('message','')[:70]}")

    print(f"\n  Solutions offered: {len(solutions)}")
    for s in solutions[:3]:
        tag = s.get('title','?')
        cmp = s.get('complexity','?')
        print(f"    [{s.get('index','-')}] {tag}  |  complexity: {cmp}")
        if s.get('code_fix'):
            snippet = s['code_fix'].strip().splitlines()[0][:72]
            print(f"        code hint → {snippet}")

# ──────────────────────────────────────────────────────────────
# TEST 2 – Security scan of the buggy Python file
# ──────────────────────────────────────────────────────────────
section("TEST 2 · Security Scan  →  examples/test_python.py")

sec = security_check(py_code)
if "error" in sec:
    print(f"  ⚠️  {sec['error']}")
else:
    score = sec.get("security_score", "?")
    issues = sec.get("issues", [])
    print(f"\n  Security Score: {score}/100")
    print(f"  Issues found  : {len(issues)}")
    for iss in issues:
        sev = iss.get("severity","?").upper()
        print(f"    [{sev}] {iss.get('type','?')} — {iss.get('message','')[:70]}")
    advice = sec.get("recommendations", [])
    if advice:
        print("\n  Recommendations:")
        for a in advice[:3]:
            print(f"    → {a}")

# ──────────────────────────────────────────────────────────────
# TEST 3 – Run the buggy Node.js file
# ──────────────────────────────────────────────────────────────
section("TEST 3 · Buggy Node.js  →  examples/test_node.js")

js_stdout, js_stderr, js_code = run(["node", str(EXAMPLES / "test_node.js")])
js_error = js_stderr or js_stdout
print(f"\n[Exit code: {js_code}]")
print("\n[RUNTIME ERROR CAPTURED]")
print(textwrap.indent(js_error.strip()[:600], "  "))

if js_error.strip():
    print("\n[SENDING TO POLYHEAL BACKEND…]")
    js_code_text = (EXAMPLES / "test_node.js").read_text()
    js_result = run_command_api(f"node {EXAMPLES / 'test_node.js'}", js_code_text)
    if "error" in js_result:
        print(f"  ⚠️  {js_result['error']}")
    else:
        errs = js_result.get("detected_errors", [])
        solutions = js_result.get("solutions", [])
        print(f"  Errors detected  : {len(errs)}")
        for e in errs[:3]:
            print(f"    • {e.get('type','?')} — {e.get('message','')[:70]}")
        print(f"  Solutions offered: {len(solutions)}")
        for s in solutions[:2]:
            print(f"    [{s.get('index','-')}] {s.get('title','?')}")

# ──────────────────────────────────────────────────────────────
# TEST 4 – Password strength checker
# ──────────────────────────────────────────────────────────────
section("TEST 4 · Password Strength Checker")

passwords = ["admin123", "P@55w0rd!", "123456", "PolyHeal$2026#Secure"]
try:
    import requests
    for pw in passwords:
        r = requests.post("http://localhost:8000/password-check",
                          json={"password": pw}, timeout=8)
        if r.status_code == 200:
            d = r.json()
            score  = d.get("score", "?")
            rating = d.get("strength", "?")
            tips   = d.get("suggestions", [])
            tip    = tips[0] if tips else "—"
            print(f"  {pw:<25} → [{rating.upper():8}] score:{score}  tip: {tip}")
except Exception as e:
    print(f"  ⚠️  {e}")

# ──────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  ALL TESTS COMPLETE — open http://localhost:5173 to see")
print("  the live dashboard results.")
print(SEP)
