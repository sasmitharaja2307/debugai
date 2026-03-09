# DEBUG AI – Multi-Language Self-Healing Developer Agent

> **An AI-powered debugging platform** that monitors developer commands, detects errors across 6 programming languages, generates multiple ranked solutions with time/space complexity analysis, and applies fixes — all from a single dashboard.

---

## What Makes POLYHEAL AI Different

| Feature | GitHub Copilot | Cursor IDE | Devin | **POLYHEAL AI** |
|---------|---------------|-----------|-------|-----------------|
| Multi-solution with complexity | ✗ | ✗ | Partial | **✓** |
| Time-travel code state diff | ✗ | ✗ | ✗ | **✓** |
| Environment awareness | ✗ | ✗ | ✗ | **✓** |
| Self-learning debug memory | ✗ | ✗ | ✗ | **✓** |
| Security analysis per fix | ✗ | ✗ | ✗ | **✓** |
| REST API for integrations | ✗ | ✗ | ✗ | **✓** |
| Multi-language (6 langs) | Partial | Partial | ✓ | **✓** |

---

## Architecture

```
polyheal/
├── backend/
│   ├── main.py                  # Entry point (CLI + server launcher)
│   ├── api_server.py            # FastAPI REST API
│   ├── agent_controller.py      # Singleton orchestrator
│   ├── command_runner.py        # Subprocess executor (Observer Pattern)
│   ├── error_detector.py        # Multi-language error parser (Strategy+Factory)
│   ├── environment_analyzer.py  # .env / requirements / package.json inspector
│   ├── code_state_tracker.py    # Time-travel snapshot system
│   ├── solution_generator.py    # LLM multi-solution generator
│   ├── security_checker.py      # Fix security auditor + password validator
│   ├── complexity_analyzer.py   # Big-O complexity estimator
│   ├── memory_store.py          # Self-learning debug case store (Singleton)
│   ├── config.py                # Centralized configuration
│   ├── languages/
│   │   ├── python_handler.py
│   │   ├── java_handler.py
│   │   ├── javascript_handler.py
│   │   ├── go_handler.py
│   │   ├── c_handler.py
│   │   └── cpp_handler.py
│   ├── search/
│   │   ├── google_search.py
│   │   ├── stackoverflow_search.py
│   │   ├── github_issue_search.py
│   │   └── documentation_retriever.py  # Search aggregator
│   └── utils/
│       ├── logger.py
│       └── patch_applier.py
├── frontend/                    # React + TailwindCSS + Framer Motion
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js
│   │   └── components/
│   │       ├── CommandPanel.jsx      # Terminal input + runner
│   │       ├── SolutionPanel.jsx     # Multi-solution comparison cards
│   │       ├── EnvironmentPanel.jsx  # Environment health dashboard
│   │       ├── SecurityPanel.jsx     # Security scanner + password checker
│   │       ├── ErrorHistory.jsx      # Debug memory viewer
│   │       └── CodeStateDiff.jsx     # Time-travel state viewer
│   └── package.json
├── extension/
│   └── vscode_extension/        # VS Code extension with webview solutions
├── requirements.txt
├── .env.example
└── start_backend.ps1
```

---

## Quick Start

### 1. Install Python dependencies

```bash
cd polyheal
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY or GEMINI_API_KEY
```

### 3. Start the backend API

```powershell
# Windows PowerShell
.\start_backend.ps1

# Or directly:
uvicorn backend.api_server:app --reload --port 8000
```

### 4. Start the frontend dashboard

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 5. API is live at

```
http://localhost:8000/docs    ← Interactive Swagger UI
http://localhost:8000/redoc   ← ReDoc documentation
```

---

## REST API Reference

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/run-command` | Run a developer command + get AI solutions |
| `POST` | `/analyze-error` | Directly analyze a known error |
| `GET` | `/environment-status` | Project environment health check |
| `GET` | `/error-history` | Debugging memory (past cases) |
| `POST` | `/apply-solution` | Apply a chosen fix |
| `GET` | `/code-state` | Project snapshot history |
| `POST` | `/security-check` | Scan code for vulnerabilities |
| `POST` | `/password-check` | Validate password strength |

---

## Supported Languages

| Language | Run Command | Error Detection |
|----------|-------------|----------------|
| Python   | `python app.py` | Traceback, ImportError, SyntaxError … |
| Java     | `java Main` | Exceptions, NullPointerException … |
| JavaScript | `node app.js` | TypeError, ReferenceError, MODULE_NOT_FOUND |
| Go       | `go run main.go` | Panic, nil dereference, undefined |
| C        | `gcc main.c -o main` | Compilation errors, segfault |
| C++      | `g++ main.cpp -o main` | Template errors, linker errors |

---

## Design Patterns Used

| Pattern | Where |
|---------|-------|
| **Singleton** | `AgentController`, `MemoryStore` |
| **Observer** | `CommandRunner` notifies subscribers |
| **Strategy** | Per-language error detection strategies |
| **Factory** | `ErrorDetector` creates the right strategy |
| **Command** | `PatchApplier` encapsulates safe patch ops |

---

## VS Code Extension

```bash
cd extension/vscode_extension
npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host
```

Commands available:
- `PolyHeal: Run & Heal Command` — runs a command and shows AI solutions in a webview
- `PolyHeal: Analyze Selected Code` — security-scans highlighted code
- `PolyHeal: Check Environment` — inspects project config files
- `PolyHeal: Open Dashboard` — opens the React dashboard

---

## Environment Variables

See `.env.example` for all available options.

**Required for AI solutions:**
```
OPENAI_API_KEY=sk-...      # or GEMINI_API_KEY
LLM_PROVIDER=openai        # or gemini
```

**Optional search enrichment:**
```
SERPAPI_KEY=...             # Google search results
GITHUB_TOKEN=...            # Higher GitHub API rate limits
```
