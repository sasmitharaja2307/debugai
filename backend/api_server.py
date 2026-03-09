"""
POLYHEAL AI – FastAPI REST API Server
Exposes all agent capabilities as HTTP endpoints.
"""

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent_controller import AgentController
from backend.security_checker import SecurityChecker
from backend.utils.logger import get_logger

log = get_logger(__name__)

app = FastAPI(
    title="POLYHEAL AI API",
    description="Multi-Language Self-Healing Developer Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-init the agent (uses project root from env)
_PROJECT_ROOT = os.getenv("POLYHEAL_PROJECT_ROOT", ".")
_agent: Optional[AgentController] = None


def get_agent() -> AgentController:
    global _agent
    if _agent is None:
        _agent = AgentController(project_root=_PROJECT_ROOT)
    return _agent


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class RunCommandRequest(BaseModel):
    command: str
    code_snippet: Optional[str] = ""
    search_summary: Optional[str] = ""


class AnalyzeErrorRequest(BaseModel):
    language: str
    error_type: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    code_snippet: Optional[str] = ""


class ApplySolutionRequest(BaseModel):
    solution: Dict[str, Any]
    target_file: Optional[str] = None


class PasswordCheckRequest(BaseModel):
    password: str


class SecurityCheckRequest(BaseModel):
    code: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "service": "POLYHEAL AI", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}


@app.post("/run-command", tags=["agent"])
async def run_command(body: RunCommandRequest):
    """
    Execute a developer command and return errors + multi-solutions.
    """
    try:
        report = get_agent().run_and_heal(
            command=body.command,
            code_snippet=body.code_snippet or "",
            search_summary=body.search_summary or "",
        )
        return report
    except Exception as exc:
        log.error("/run-command error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/analyze-error", tags=["agent"])
async def analyze_error(body: AnalyzeErrorRequest):
    """
    Directly analyze a known error and return solutions.
    """
    try:
        from backend.solution_generator import SolutionGenerator

        gen = SolutionGenerator()
        solutions = gen.generate(
            error=body.dict(),
            code_snippet=body.code_snippet or "",
        )
        return {"solutions": [s.to_dict() for s in solutions]}
    except Exception as exc:
        log.error("/analyze-error error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/environment-status", tags=["environment"])
async def environment_status():
    """
    Return current environment health and detected issues.
    """
    return get_agent().get_environment_status()


@app.get("/error-history", tags=["memory"])
async def error_history():
    """
    Return recent debugging history from memory store.
    """
    return {"history": get_agent().get_error_history()}


@app.post("/apply-solution", tags=["agent"])
async def apply_solution(body: ApplySolutionRequest):
    """
    Apply a selected solution (run command + patch file).
    """
    try:
        result = get_agent().apply_solution(
            solution=body.solution,
            target_file=body.target_file,
        )
        return result
    except Exception as exc:
        log.error("/apply-solution error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/code-state", tags=["tracking"])
async def code_state():
    """
    Return project snapshot history and last successful state.
    """
    return get_agent().get_code_state()


@app.post("/security-check", tags=["security"])
async def security_check(body: SecurityCheckRequest):
    """
    Run a security scan on a code snippet.
    """
    checker = SecurityChecker()
    report = checker.check(body.code)
    return report.to_dict()


@app.post("/password-check", tags=["security"])
async def password_check(body: PasswordCheckRequest):
    """
    Validate password strength.
    """
    checker = SecurityChecker()
    return checker.validate_password(body.password)
