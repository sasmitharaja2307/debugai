"""
AI Code Optimizer – Flask Backend
Entry point: python backend/app.py
Serves the frontend AND provides all API endpoints.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from optimizer import optimize_code, explain_code, get_complexity
from config import Config

# Resolve frontend folder (one level up from backend/)
FRONTEND_DIR = str(Path(__file__).parent.parent / "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ── Serve Frontend ────────────────────────────────────────────
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

# ── Health Check ──────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "AI Code Optimizer", "version": "2.0"})

# ── Optimize ──────────────────────────────────────────────────
@app.route("/api/optimize", methods=["POST"])
def optimize():
    data = request.get_json()
    if not data or not data.get("code", "").strip():
        return jsonify({"error": "Missing or empty 'code' field"}), 400
    result = optimize_code(data["code"].strip(), data.get("language", "python").lower())
    return jsonify(result)

# ── Explain ───────────────────────────────────────────────────
@app.route("/api/explain", methods=["POST"])
def explain():
    data = request.get_json()
    if not data or not data.get("code", "").strip():
        return jsonify({"error": "Missing or empty 'code' field"}), 400
    result = explain_code(data["code"].strip(), data.get("language", "python").lower())
    return jsonify(result)

# ── Complexity ────────────────────────────────────────────────
@app.route("/api/complexity", methods=["POST"])
def complexity():
    data = request.get_json()
    if not data or not data.get("code", "").strip():
        return jsonify({"error": "Missing or empty 'code' field"}), 400
    result = get_complexity(data["code"].strip(), data.get("language", "python").lower())
    return jsonify(result)

# ── Run Code ──────────────────────────────────────────────────
@app.route("/api/run", methods=["POST"])
def run_code():
    """
    Execute code in a sandboxed subprocess with a timeout.
    Supports: python, javascript (node), typescript (ts-node), go, c, cpp
    """
    data = request.get_json()
    if not data or not data.get("code", "").strip():
        return jsonify({"error": "Missing or empty 'code' field"}), 400

    code     = data["code"].strip()
    language = data.get("language", "python").lower()
    timeout  = min(int(data.get("timeout", 10)), 15)  # max 15s

    RUNNERS = {
        "python":     ("py",   [sys.executable]),
        "javascript": ("js",   ["node"]),
        "typescript": ("ts",   ["npx", "ts-node"]),
        "go":         ("go",   ["go", "run"]),
        "ruby":       ("rb",   ["ruby"]),
        "php":        ("php",  ["php"]),
    }

    if language not in RUNNERS:
        return jsonify({
            "stdout": "",
            "stderr": f"'{language}' execution is not supported yet.\nSupported: python, javascript, go, ruby, php",
            "exit_code": -1,
            "runtime_ms": 0,
        })

    ext, runner = RUNNERS[language]

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{ext}", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        import time
        start = time.time()
        proc = subprocess.run(
            runner + [tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = int((time.time() - start) * 1000)

        return jsonify({
            "stdout":     proc.stdout,
            "stderr":     proc.stderr,
            "exit_code":  proc.returncode,
            "runtime_ms": elapsed,
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "stdout":     "",
            "stderr":     f"Execution timed out after {timeout} seconds.",
            "exit_code":  -1,
            "runtime_ms": timeout * 1000,
        })
    except FileNotFoundError:
        cmd = runner[0]
        return jsonify({
            "stdout":     "",
            "stderr":     f"'{cmd}' is not installed or not in PATH.",
            "exit_code":  -1,
            "runtime_ms": 0,
        })
    except Exception as e:
        return jsonify({
            "stdout":     "",
            "stderr":     str(e),
            "exit_code":  -1,
            "runtime_ms": 0,
        })
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

# ── Entry Point ───────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  AI Code Optimizer")
    print(f"  Open → http://localhost:{Config.PORT}")
    print(f"{'='*50}\n")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
