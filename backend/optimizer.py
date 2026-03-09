"""
AI Code Optimizer – Core Optimization Engine
Supports: Python (AST), JavaScript, Java, Go, C/C++, and more via rules.
Uses OpenAI GPT when API key is set, smart offline engine otherwise.
"""

import ast
import difflib
import json
import re
import builtins
from typing import Optional
from config import Config

# ── OpenAI Setup ──────────────────────────────────────────────
try:
    import openai as _openai_mod
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False


def _get_client():
    if not _HAS_OPENAI or not Config.OPENAI_API_KEY:
        return None
    try:
        import openai
        return openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    except Exception:
        return None


# ── Prompt Templates ──────────────────────────────────────────
_OPTIMIZE_PROMPT = """\
You are an expert code optimizer. Analyze the following {language} code.
Return ONLY a valid JSON object (no markdown fences) with these keys:
  "optimized_code"   : string  – the improved code
  "improvements"     : array   – list of changes made (each a string)
  "performance_gain" : string  – e.g. "40% faster"
  "readability_score": integer – 1-10

Code:
```{language}
{code}
```"""

_EXPLAIN_PROMPT = """\
You are a senior software engineer. Explain the following {language} code.
Return ONLY a valid JSON object (no markdown fences) with:
  "explanation"     : string – plain English, what it does
  "key_concepts"    : array  – programming concepts used
  "potential_issues": array  – bugs or issues found
  "suggestions"     : array  – improvement ideas

Code:
```{language}
{code}
```"""

_COMPLEXITY_PROMPT = """\
Analyze the time and space complexity of this {language} code.
Return ONLY a valid JSON object (no markdown fences) with:
  "time_complexity" : string – Big-O time  (e.g. "O(n log n)")
  "space_complexity": string – Big-O space (e.g. "O(n)")
  "summary"         : string – one sentence explanation
  "bottleneck"      : string – main performance bottleneck

Code:
```{language}
{code}
```"""


# ── GPT Call ──────────────────────────────────────────────────
def _call_gpt(prompt: str) -> dict:
    client = _get_client()
    if not client:
        return {"error": "no_key"}
    try:
        resp = client.chat.completions.create(
            model=Config.MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"```(?:json)?\n?", "", raw).strip().rstrip("`")
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "parse_failed"}
    except Exception as e:
        return {"error": str(e)}


# ── Python AST Analyzer ───────────────────────────────────────
def _analyze_python(code: str) -> dict:
    """
    Full Python analysis via AST:
    - SyntaxError detection with line number
    - Undefined variable detection + typo correction
    - Style + best-practice checks
    - Security scanning
    Returns {"improvements": [...], "fixed_code": str, "issues": int}
    """
    improvements = []
    optimized    = code

    # 1. Syntax check
    try:
        compile(code, "<string>", "exec")
    except SyntaxError as e:
        improvements.append(f"[SYNTAX ERROR] Line {e.lineno}: {e.msg}")

    # 2. AST undefined-variable / typo detection
    try:
        tree   = ast.parse(code)
        defined: set = set(dir(builtins))

        class _Definer(ast.NodeVisitor):
            def visit_Assign(self, node):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        defined.add(t.id)
                    elif isinstance(t, (ast.Tuple, ast.List)):
                        for e in t.elts:
                            if isinstance(e, ast.Name): defined.add(e.id)
                self.generic_visit(node)
            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name): defined.add(node.target.id)
                self.generic_visit(node)
            def visit_FunctionDef(self, node):
                defined.add(node.name)
                for a in node.args.args: defined.add(a.arg)
                for a in (node.args.posonlyargs + node.args.kwonlyargs): defined.add(a.arg)
                if node.args.vararg:   defined.add(node.args.vararg.arg)
                if node.args.kwarg:    defined.add(node.args.kwarg.arg)
                self.generic_visit(node)
            visit_AsyncFunctionDef = visit_FunctionDef
            def visit_ClassDef(self, node):
                defined.add(node.name); self.generic_visit(node)
            def visit_For(self, node):
                if isinstance(node.target, ast.Name): defined.add(node.target.id)
                elif isinstance(node.target, (ast.Tuple, ast.List)):
                    for e in node.target.elts:
                        if isinstance(e, ast.Name): defined.add(e.id)
                self.generic_visit(node)
            def visit_Import(self, node):
                for a in node.names: defined.add(a.asname or a.name.split(".")[0])
                self.generic_visit(node)
            def visit_ImportFrom(self, node):
                for a in node.names: defined.add(a.asname or a.name)
                self.generic_visit(node)
            def visit_With(self, node):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        defined.add(item.optional_vars.id)
                self.generic_visit(node)
            def visit_NamedExpr(self, node):
                if isinstance(node.target, ast.Name): defined.add(node.target.id)
                self.generic_visit(node)
            def visit_Global(self, node):
                for n in node.names: defined.add(n)
                self.generic_visit(node)
            def visit_Nonlocal(self, node):
                for n in node.names: defined.add(n)
                self.generic_visit(node)
            def visit_comprehension(self, node):
                if isinstance(node.target, ast.Name): defined.add(node.target.id)
                self.generic_visit(node)

        _Definer().visit(tree)

        seen_undef: set = set()

        class _Finder(ast.NodeVisitor):
            def visit_Name(inner_self, node):
                if (
                    isinstance(node.ctx, ast.Load)
                    and node.id not in defined
                    and not node.id.startswith("__")
                    and node.id not in seen_undef
                ):
                    seen_undef.add(node.id)
                    user_names = [n for n in defined if len(n) > 2 and not n.startswith("_")]
                    matches = difflib.get_close_matches(node.id, user_names, n=1, cutoff=0.55)
                    nonlocal optimized
                    if matches:
                        fix = matches[0]
                        improvements.append(
                            f"[BUG] Line {node.lineno}: '{node.id}' is not defined — "
                            f"did you mean '{fix}'? (auto-fixed)"
                        )
                        optimized = re.sub(r'\b' + re.escape(node.id) + r'\b', fix, optimized)
                    else:
                        improvements.append(
                            f"[BUG] Line {node.lineno}: '{node.id}' is not defined"
                        )
                inner_self.generic_visit(node)

        _Finder().visit(tree)

    except SyntaxError:
        pass

    # 3. Style & performance checks
    checks = [
        (r"range\(len\(",           "Style: Use enumerate() instead of range(len())"),
        (r"\.append\(",             "Performance: Consider list comprehension instead of .append() in loop"
                                    if "for " in code else None),
        (r"==\s*True|==\s*False",   "Style: Use 'if x:' / 'if not x:' instead of '== True/False'"),
        (r"except\s*:",             "Best practice: Catch specific exceptions, not bare 'except:'"),
        (r"\beval\s*\(",            "[SECURITY] Avoid eval() — it can execute arbitrary code"),
        (r"\bexec\s*\(",            "[SECURITY] Avoid exec() — it can execute arbitrary code"),
        (r"import \*",              "Style: Avoid 'import *' — import only what you need"),
        (r"(?m)^(\s{1,3})\S",      "Style: Use 4-space indentation (PEP 8)"),
    ]
    seen = set()
    for pattern, msg in checks:
        if msg and pattern not in seen and re.search(pattern, code):
            seen.add(pattern)
            improvements.append(msg)

    # 4. Security checks
    if re.search(r'(password|api_key|secret|token)\s*=\s*["\']', code, re.IGNORECASE):
        improvements.append("[SECURITY] Hardcoded credentials — move to environment variables")
    if "open(" in code and "try:" not in code:
        improvements.append("Safety: Wrap file I/O in try/except to handle missing files")

    bug_count = len([i for i in improvements if i.startswith("[BUG]") or i.startswith("[SYNTAX")])
    return {
        "improvements": improvements or ["No issues detected. Good code!"],
        "fixed_code":   optimized,
        "issue_count":  len(improvements),
        "bug_count":    bug_count,
        "readability":  max(3, 10 - bug_count * 2 - len([i for i in improvements if "[SECURITY]" in i]))
    }


# ── Generic Multi-Language Rule Engine ───────────────────────
def _analyze_generic(code: str, language: str) -> dict:
    """Rule-based analysis for JS, Java, Go, C, C++, etc."""
    improvements = []
    lines        = code.splitlines()
    line_count   = len(lines)

    if language in ("javascript", "typescript"):
        if re.search(r'\bvar\b', code):
            improvements.append("Style: Use 'const' or 'let' instead of 'var' (ES6+)")
        if re.search(r'==(?!=)', code):
            improvements.append("Style: Use '===' instead of '==' to avoid type coercion")
        if re.search(r'console\.log', code):
            improvements.append("Clean-up: Remove console.log() calls before production")
        if re.search(r'\.then\(', code) and "async" not in code:
            improvements.append("Modern JS: Consider async/await instead of .then() chains")
        if not re.search(r'try\s*{', code) and re.search(r'fetch|axios|http', code):
            improvements.append("Safety: Wrap network calls in try/catch for error handling")
        if re.search(r'require\s*\(', code) and "import" not in code:
            improvements.append("Style: Use ES6 'import' instead of CommonJS 'require()'")
        if re.search(r'(password|api_?key|secret|token)\s*[=:]', code, re.IGNORECASE):
            improvements.append("[SECURITY] Hardcoded credentials — use environment variables")

    elif language == "java":
        if re.search(r'System\.out\.print', code):
            improvements.append("Production: Replace System.out.println with a proper logger (SLF4J/Log4j)")
        if re.search(r'catch\s*\(\s*Exception\s+', code):
            improvements.append("Best practice: Catch specific exceptions instead of generic Exception")
        if re.search(r'String\s+\w+\s*=\s*""\s*;', code) and '+=' in code:
            improvements.append("Performance: Use StringBuilder instead of string concatenation with +=")
        if not re.search(r'@Override', code) and re.search(r'\bequals\b|\bhashCode\b', code):
            improvements.append("Best practice: Add @Override annotation when overriding equals/hashCode")

    elif language == "go":
        if re.search(r'fmt\.Print', code) and not re.search(r'log\.', code):
            improvements.append("Style: Use the 'log' package instead of fmt.Print for logging")
        if re.search(r'if err != nil', code) and code.count("if err != nil") > 3:
            improvements.append("Refactor: Consider wrapping repeated error checks into a helper function")
        if re.search(r'panic\(', code):
            improvements.append("Best practice: Avoid panic() in production — return errors instead")

    elif language in ("c", "cpp"):
        if re.search(r'gets\s*\(', code):
            improvements.append("[SECURITY] Never use gets() — use fgets() instead (buffer overflow risk)")
        if re.search(r'scanf\s*\(\s*"%s"', code):
            improvements.append("[SECURITY] Use scanf(\"%Ns\") with a limit to prevent buffer overflow")
        if re.search(r'malloc\s*\(', code) and not re.search(r'free\s*\(', code):
            improvements.append("Memory: Every malloc() should have a corresponding free() — possible leak")
        if language == "cpp":
            if re.search(r'\bmalloc\b|\bfree\b', code):
                improvements.append("C++ style: Prefer 'new/delete' or smart pointers over malloc/free")
            if re.search(r'using namespace std', code):
                improvements.append("Best practice: Avoid 'using namespace std' in headers")

    # Universal rules
    lines_over_80 = [i+1 for i, l in enumerate(lines) if len(l) > 120]
    if lines_over_80:
        improvements.append(
            f"Style: Lines {', '.join(str(x) for x in lines_over_80[:3])}{'…' if len(lines_over_80)>3 else ''} exceed 120 chars"
        )

    if re.search(r'(password|api.?key|secret)\s*[=:]', code, re.IGNORECASE):
        improvements.append("[SECURITY] Hardcoded credentials — use environment variables")

    bug_count = len([i for i in improvements if "[SECURITY]" in i])
    return {
        "improvements": improvements or ["Code looks clean for a rule-based check. Add an OpenAI API key for deep AI analysis."],
        "fixed_code":   code,  # no auto-fix for non-Python
        "issue_count":  len(improvements),
        "bug_count":    bug_count,
        "readability":  max(4, 10 - len(improvements))
    }


# ── Complexity Heuristics ─────────────────────────────────────
def _complexity_heuristic(code: str) -> dict:
    nested  = len(re.findall(r'for .+:\s*\n\s+for .+:', code))
    triple  = len(re.findall(r'for .+:\s*\n(?:\s+.+\n)*\s+for .+:\s*\n(?:\s+.+\n)*\s+for .+:', code))
    loops   = len(re.findall(r'\bfor\b|\bwhile\b', code))
    recur   = bool(re.search(r'def (\w+).*:\n(?:.*\n)*?.*\1\s*\(', code))
    sorting = bool(re.search(r'\.sort\b|sorted\b|merge.?sort|quick.?sort|heap.?sort', code, re.IGNORECASE))
    binary  = bool(re.search(r'binary.?search|bisect', code, re.IGNORECASE))

    if triple:
        tc, note = "O(n³)", "Triple-nested loops"
    elif nested:
        tc, note = "O(n²)", "Nested loops (consider sorting + binary search)"
    elif sorting:
        tc, note = "O(n log n)", "Sorting operation dominates"
    elif binary:
        tc, note = "O(log n)", "Binary search"
    elif recur:
        tc, note = "O(2ⁿ) worst / O(n log n) avg", "Recursive calls"
    elif loops:
        tc, note = "O(n)", "Single loop iteration"
    else:
        tc, note = "O(1)", "No loops or recursion"

    has_ds   = bool(re.search(r'\[\]|{|}|list\(|dict\(|set\(', code))
    sc = "O(n)" if has_ds else "O(1)"

    return {"time_complexity": tc, "space_complexity": sc,
            "summary": f"Estimated {tc} — {note}.", "bottleneck": note}


# ── Public API ────────────────────────────────────────────────
def optimize_code(code: str, language: str = "python") -> dict:
    # Try AI first
    if Config.OPENAI_API_KEY:
        prompt = _OPTIMIZE_PROMPT.format(language=language, code=code)
        r = _call_gpt(prompt)
        if "error" not in r:
            r.update({"original": code, "mode": "ai"})
            return r

    # Offline engine
    if language == "python":
        analysis = _analyze_python(code)
    else:
        analysis = _analyze_generic(code, language)

    return {
        "original":         code,
        "optimized_code":   analysis["fixed_code"],
        "improvements":     analysis["improvements"],
        "performance_gain": "Bug(s) auto-fixed" if analysis["fixed_code"] != code else "Review suggestions above",
        "readability_score": analysis["readability"],
        "issue_count":      analysis["issue_count"],
        "mode":             "offline",
    }


def explain_code(code: str, language: str = "python") -> dict:
    # Try AI first
    if Config.OPENAI_API_KEY:
        prompt = _EXPLAIN_PROMPT.format(language=language, code=code)
        r = _call_gpt(prompt)
        if "error" not in r:
            r["mode"] = "ai"
            return r

    # Offline fallback using our static analysis
    if language == "python":
        analysis = _analyze_python(code)
    else:
        analysis = _analyze_generic(code, language)

    lines    = code.strip().splitlines()
    has_func = bool(re.search(r'\bdef\b|\bfunction\b|\bfunc\b', code))
    has_loop = bool(re.search(r'\bfor\b|\bwhile\b', code))
    has_cls  = bool(re.search(r'\bclass\b', code))
    has_try  = bool(re.search(r'\btry\b|\bcatch\b|\bexcept\b', code))

    concepts = []
    if has_func: concepts.append("Functions / Methods")
    if has_loop: concepts.append("Loops / Iteration")
    if has_cls:  concepts.append("Classes / OOP")
    if has_try:  concepts.append("Error handling")
    if not concepts: concepts = ["Variables", "Basic logic"]

    issues = [i for i in analysis["improvements"] if i.startswith("[")]
    if not issues:
        issues = ["No obvious bugs found (add OpenAI key for deep AI analysis)"]

    description = (
        f"{language.capitalize()} snippet ({len(lines)} lines). "
        + ("Defines functions. " if has_func else "")
        + ("Uses loops. " if has_loop else "")
        + ("Uses classes. " if has_cls else "")
        + ("Has error handling. " if has_try else "")
    ).strip()

    return {
        "explanation":      description,
        "key_concepts":     concepts,
        "potential_issues": issues,
        "suggestions":      analysis["improvements"],
        "mode":             "offline",
    }


def get_complexity(code: str, language: str = "python") -> dict:
    # Try AI first
    if Config.OPENAI_API_KEY:
        prompt = _COMPLEXITY_PROMPT.format(language=language, code=code)
        r = _call_gpt(prompt)
        if "error" not in r:
            r["mode"] = "ai"
            return r

    result = _complexity_heuristic(code)
    result["mode"] = "offline"
    return result
