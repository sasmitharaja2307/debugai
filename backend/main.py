"""
POLYHEAL AI – Entry Point
Run with:  uvicorn backend.main:app --reload --port 8000
Or CLI:    python -m backend.main run "python app.py"
"""

import sys

import uvicorn

from backend.api_server import app
from backend.utils.logger import get_logger

log = get_logger("polyheal.main")


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True) -> None:
    """Launch the FastAPI server."""
    log.info("Starting POLYHEAL AI API server on %s:%d", host, port)
    uvicorn.run("backend.api_server:app", host=host, port=port, reload=reload)


def cli_run(command: str, project_root: str = ".") -> None:
    """CLI helper: run a single command through the agent and print the report."""
    import json
    from backend.agent_controller import AgentController

    agent = AgentController(project_root=project_root)
    report = agent.run_and_heal(command)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "serve":
        start_server()
    elif args[0] == "run" and len(args) > 1:
        cli_run(" ".join(args[1:]))
    else:
        print("Usage:")
        print("  python -m backend.main serve         # Start API server")
        print("  python -m backend.main run <cmd>     # Run a command via CLI")
