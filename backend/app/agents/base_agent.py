"""
Base class all pipeline agents inherit from.

Each agent receives a shared `context` dict that flows through the pipeline
(IntentAgent -> PlanningAgent -> DataAgent -> ExecutionAgent -> AnalyticsAgent
-> ReportingAgent). Agents read what they need from context and write their
output back into it under their own key, plus emit log lines via `log()`
which the orchestrator persists to the job's log stream.
"""
from typing import Any, Callable, Dict, Optional


class BaseAgent:
    name: str = "base_agent"

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        log_callback(agent_name, message) -> None
        Passed in by the orchestrator so agents can stream progress without
        knowing about the database/job model directly.
        """
        self._log_callback = log_callback

    def log(self, message: str) -> None:
        if self._log_callback:
            self._log_callback(self.name, message)

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Subclasses override this. Must return the (mutated) context dict.
        """
        raise NotImplementedError
