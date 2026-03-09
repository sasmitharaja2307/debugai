"""
POLYHEAL AI – Agent Controller
Singleton orchestrator that ties all modules together.
Follows Observer + Strategy + Singleton patterns.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from backend.code_state_tracker import CodeStateTracker
from backend.command_runner import CommandRunner, RunResult
from backend.environment_analyzer import EnvironmentAnalyzer
from backend.error_detector import DetectedError, ErrorDetector
from backend.memory_store import DebugCase, MemoryStore
from backend.security_checker import SecurityChecker
from backend.solution_generator import Solution, SolutionGenerator
from backend.utils.logger import get_logger
from backend.utils.patch_applier import PatchApplier

log = get_logger(__name__)


class AgentController:
    """
    Singleton: only one instance orchestrates the whole debugging pipeline.

    Pipeline:
      1. Snapshot project state
      2. Run developer command (Observer notifies controller)
      3. Detect errors
      4. Analyze environment
      5. Search for context (injected externally)
      6. Generate multi-solutions
      7. Store result in memory
      8. Return full report
    """

    _instance: Optional["AgentController"] = None

    def __new__(cls, project_root: str = "."):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._initialized = False
            cls._instance = obj
        return cls._instance

    def __init__(self, project_root: str = "."):
        if self._initialized:
            return

        self.project_root = project_root
        self._runner = CommandRunner(cwd=project_root)
        self._detector = ErrorDetector()
        self._env_analyzer = EnvironmentAnalyzer(project_root)
        self._state_tracker = CodeStateTracker(project_root)
        self._solution_gen = SolutionGenerator()
        self._security = SecurityChecker()
        self._memory = MemoryStore(project_root)
        self._patch = PatchApplier(project_root)

        # Subscribe to run events
        self._runner.subscribe(self._on_run_complete)

        self._last_report: Optional[dict] = None
        self._initialized = True
        log.info("AgentController initialized for project: %s", project_root)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run_and_heal(
        self,
        command: str,
        code_snippet: str = "",
        search_summary: str = "",
    ) -> dict:
        """
        Full debugging pipeline. Returns a comprehensive report.
        """
        run_id = str(uuid.uuid4())[:8]
        log.info("=== PolyHeal Run [%s] === command: %s", run_id, command)

        # 1. Pre-run environment analysis
        env_issues = self._env_analyzer.analyze()
        env_context = "\n".join(f"[{i.severity}] {i.message}" for i in env_issues)

        # 2. Take pre-run snapshot
        self._state_tracker.take_snapshot(run_id + "_before", command, success=True)

        # 3. Execute command
        result: RunResult = self._runner.run(command)

        # 4. Take post-run snapshot
        self._state_tracker.take_snapshot(run_id + "_after", command, success=result.success)

        # 5. Detect errors
        errors: List[DetectedError] = self._detector.detect(
            command, result.stdout, result.stderr, result.returncode
        )

        # 6. State diff analysis
        last_good = self._state_tracker.last_successful_snapshot()
        current = self._state_tracker.latest_snapshot()
        state_diff = None
        if last_good and current and not result.success:
            state_diff = self._state_tracker.diff(last_good, current).to_dict()

        # 7. Find similar past cases from memory
        memory_suggestions: List[dict] = []
        if errors:
            similar = self._memory.find_similar(errors[0].message, errors[0].language)
            memory_suggestions = [
                {
                    "case_id": c.case_id,
                    "solution_title": c.solution_title,
                    "fix_command": c.fix_command,
                    "was_successful": c.was_successful,
                }
                for c in similar
            ]

        # 8. Generate solutions (for first error)
        solutions: List[Solution] = []
        if errors:
            solutions = self._solution_gen.generate(
                error=errors[0].to_dict(),
                code_snippet=code_snippet,
                env_context=env_context,
                search_summary=search_summary,
            )

        report = {
            "run_id": run_id,
            "command": command,
            "success": result.success,
            "run_result": result.to_dict(),
            "errors": [e.to_dict() for e in errors],
            "environment_issues": [i.to_dict() for i in env_issues],
            "state_diff": state_diff,
            "memory_suggestions": memory_suggestions,
            "solutions": [s.to_dict() for s in solutions],
            "timestamp": time.time(),
        }
        self._last_report = report
        log.info("Run [%s] complete. Errors: %d, Solutions: %d", run_id, len(errors), len(solutions))
        return report

    # ------------------------------------------------------------------
    # Apply a chosen solution
    # ------------------------------------------------------------------

    def apply_solution(
        self,
        solution: dict,
        target_file: Optional[str] = None,
    ) -> dict:
        results = []

        fix_command = solution.get("fix_command", "").strip()
        code_patch = solution.get("code_patch", "").strip()

        if fix_command:
            cmd_result = self._patch.apply_shell_command(fix_command)
            results.append({"type": "command", "result": cmd_result})

        if code_patch and target_file:
            patch_result = self._patch.apply_file_patch(target_file, code_patch)
            results.append({"type": "file_patch", "result": patch_result})

        # Persist to memory
        if self._last_report and self._last_report.get("errors"):
            err = self._last_report["errors"][0]
            case = DebugCase(
                case_id=str(uuid.uuid4())[:8],
                timestamp=time.time(),
                language=err.get("language", "unknown"),
                error_type=err.get("error_type", "Error"),
                error_message=err.get("message", ""),
                solution_title=solution.get("title", ""),
                solution_code=solution.get("code_patch", ""),
                fix_command=solution.get("fix_command", ""),
                was_successful=True,
                tags=solution.get("tags", []),
            )
            self._memory.store(case)

        return {"status": "applied", "results": results}

    # ------------------------------------------------------------------
    # Observer callback
    # ------------------------------------------------------------------

    def _on_run_complete(self, result: RunResult) -> None:
        icon = "✓" if result.success else "✗"
        log.info(
            "%s Command finished | rc=%d | %.0fms | %s",
            icon,
            result.returncode,
            result.duration_ms,
            result.command,
        )

    # ------------------------------------------------------------------
    # Status & History
    # ------------------------------------------------------------------

    def get_environment_status(self) -> dict:
        issues = self._env_analyzer.analyze()
        return {
            "issues": [i.to_dict() for i in issues],
            "issue_count": len(issues),
            "critical_count": sum(1 for i in issues if i.severity == "critical"),
        }

    def get_error_history(self) -> List[dict]:
        return self._memory.recent_cases(50)

    def get_code_state(self) -> dict:
        return {
            "history": self._state_tracker.get_history(),
            "last_successful": (
                self._state_tracker.last_successful_snapshot().to_dict()
                if self._state_tracker.last_successful_snapshot()
                else None
            ),
        }
